from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from models.itinerary import Itinerary
from models.user import User
from schemas.itinerary import (
    ItineraryCreate,
    ItineraryUpdate,
    ItineraryGenerate,
    ItineraryDiffResponse,
    DayDiff,
    ActivityDiff,
    ProposedTrip,
    ProposedDay,
    ProposedActivity,
)
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
from graphs.itinerary_graph import itinerary_graph
from graphs.itinerary_agent import itinerary_agent
from utils.agent import is_valid_thread_state
from utils.utils import state_to_dict, detect_hil_mode
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from models.traveler_test.traveler_type import TravelerType
from langchain_openai import ChatOpenAI
from state import ViajeState
from difflib import SequenceMatcher
from langchain_core.messages import SystemMessage, HumanMessage
from models.itinerary_change_log import ItineraryChangeLog
import re

class ItineraryService:
    """Service class for itinerary CRUD operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_itinerary(self, itinerary_data: ItineraryCreate, user: Optional[User] = None, session_id: Optional[uuid.UUID] = None) -> Itinerary:
        """Create a new itinerary with automatic user/session assignment"""
        itinerary_dict = itinerary_data.dict()
        
        # Set user_id if user is authenticated, otherwise use session_id
        if user:
            itinerary_dict['user_id'] = str(user.id)  # Convert UUID to string for Auth0 compatibility
            itinerary_dict['session_id'] = None  # Clear session_id for authenticated users
        else:
            itinerary_dict['user_id'] = None
            itinerary_dict['session_id'] = session_id or uuid.uuid4()
        
        db_itinerary = Itinerary(**itinerary_dict)
        self.db.add(db_itinerary)
        self.db.commit()
        self.db.refresh(db_itinerary)
        
        # Update user trip count if authenticated
        if user:
            user.total_trips_created += 1
            self.db.commit()

        # Attach traveler_profile detail for response convenience
        try:
            if user and getattr(user, "traveler_type_id", None):
                # If user was eager-loaded, use that; else fetch
                tt_obj = getattr(user, "traveler_type", None)
                if not tt_obj:
                    try:
                        tt_obj = self.db.get(TravelerType, user.traveler_type_id)  # type: ignore[attr-defined]
                    except Exception:
                        tt_obj = self.db.query(TravelerType).get(user.traveler_type_id)  # type: ignore[attr-defined]
                if tt_obj:
                    # Non-persistent attribute for serialization layer
                    setattr(db_itinerary, "traveler_profile", tt_obj)
        except Exception:
            pass

        return db_itinerary

    def generate_itinerary(self, itinerary_data: ItineraryGenerate, user: Optional[User] = None, session_id: Optional[uuid.UUID] = None) -> Itinerary:
        """Generate an itinerary with automatic user/session assignment"""

        # 1) If authenticated, enrich generation input with user's current traveler_type
        if user and getattr(user, "traveler_type_id", None):
            # Prefer session.get in SQLAlchemy 2.x
            try:
                tt: Optional[TravelerType] = self.db.get(TravelerType, user.traveler_type_id)  # type: ignore[attr-defined]
            except Exception:
                # Fallback to legacy Query.get if needed
                tt = self.db.query(TravelerType).get(user.traveler_type_id)  # type: ignore[attr-defined]
            if tt:
                itinerary_data = ItineraryGenerate(
                    trip_name=itinerary_data.trip_name,
                    duration_days=itinerary_data.duration_days,
                    traveler_profile_name=tt.name,
                    traveler_profile_desc=tt.prompt_description or tt.description or "",
                )

        # 2) Generate state via graph with the enriched input
        state = itinerary_graph.invoke(itinerary_data)
        details_itinerary = state_to_dict(state)

        # 3) Audit: expose traveler profile used inside details_itinerary
        try:
            if isinstance(details_itinerary, dict):
                details_itinerary.setdefault("_meta", {})
                profile_meta = {
                    "name": getattr(itinerary_data, "traveler_profile_name", None),
                    "desc": getattr(itinerary_data, "traveler_profile_desc", None),
                }
                if user and getattr(user, "traveler_type_id", None):
                    profile_meta["traveler_type_id"] = str(user.traveler_type_id)
                details_itinerary["_meta"]["traveler_profile"] = profile_meta
        except Exception:
            # non-fatal: keep generation even if audit metadata fails
            pass

        # Set user_id if user is authenticated, otherwise use session_id
        if user:
            user_id = str(user.id)
            session_id_to_use = None
        else:
            user_id = None
            session_id_to_use = session_id or uuid.uuid4()

        db_itinerary = Itinerary(
            trip_name=itinerary_data.trip_name,
            duration_days=itinerary_data.duration_days,
            details_itinerary=details_itinerary,
            user_id=user_id,
            session_id=session_id_to_use
        )

        self.db.add(db_itinerary)
        self.db.commit()
        self.db.refresh(db_itinerary)
        
        # Update user trip count if authenticated
        if user:
            user.total_trips_created += 1
            self.db.commit()
        
        return db_itinerary
    
    def get_itinerary_by_id(self, itinerary_id: uuid.UUID) -> Optional[Itinerary]:
        """Get itinerary by UUID (excluding soft deleted)"""
        return self.db.query(Itinerary).filter(
            and_(
                Itinerary.itinerary_id == itinerary_id,
                Itinerary.deleted_at.is_(None)
            )
        ).first()
    
    def get_itinerary_by_slug(self, slug: str) -> Optional[Itinerary]:
        """Get itinerary by slug (excluding soft deleted)"""
        return self.db.query(Itinerary).filter(
            and_(
                Itinerary.slug == slug,
                Itinerary.deleted_at.is_(None)
            )
        ).first()
    
    def get_itineraries_by_user(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Itinerary]:
        """Get all itineraries for a specific Auth0 user"""
        return self.db.query(Itinerary).filter(
            and_(
                Itinerary.user_id == user_id,
                Itinerary.deleted_at.is_(None)
            )
        ).offset(skip).limit(limit).all()
    
    def get_itineraries_by_session(self, session_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Itinerary]:
        """Get all itineraries for a specific session UUID"""
        return self.db.query(Itinerary).filter(
            and_(
                Itinerary.session_id == session_id,
                Itinerary.deleted_at.is_(None)
            )
        ).offset(skip).limit(limit).all()
    
    def get_user_or_session_itineraries(self, user_id: Optional[str] = None, session_id: Optional[uuid.UUID] = None, 
                                      skip: int = 0, limit: int = 100) -> List[Itinerary]:
        """Get itineraries for either Auth0 user_id or session_id UUID"""
        if user_id:
            return self.get_itineraries_by_user(user_id, skip, limit)
        elif session_id:
            return self.get_itineraries_by_session(session_id, skip, limit)
        else:
            return []
    
    def get_public_itineraries(self, skip: int = 0, limit: int = 100) -> List[Itinerary]:
        """Get all public itineraries"""
        return self.db.query(Itinerary).filter(
            and_(
                Itinerary.visibility == "public",
                Itinerary.deleted_at.is_(None)
            )
        ).offset(skip).limit(limit).all()
    
    def search_itineraries(self, query: str, skip: int = 0, limit: int = 100) -> List[Itinerary]:
        """Search itineraries by trip name or destination"""
        search_filter = or_(
            Itinerary.trip_name.ilike(f"%{query}%"),
            Itinerary.destination.ilike(f"%{query}%")
        )
        return self.db.query(Itinerary).filter(
            and_(
                search_filter,
                Itinerary.visibility == "public",
                Itinerary.deleted_at.is_(None)
            )
        ).offset(skip).limit(limit).all()
    
    def update_itinerary(self, itinerary_id: uuid.UUID, itinerary_data: ItineraryUpdate) -> Optional[Itinerary]:
        """Update an existing itinerary"""
        db_itinerary = self.get_itinerary_by_id(itinerary_id)
        if not db_itinerary:
            return None
        
        update_data = itinerary_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_itinerary, field, value)
        
        self.db.commit()
        self.db.refresh(db_itinerary)
        return db_itinerary
    
    def soft_delete_itinerary(self, itinerary_id: uuid.UUID) -> bool:
        """Soft delete an itinerary"""
        db_itinerary = self.get_itinerary_by_id(itinerary_id)
        if not db_itinerary:
            return False
        
        db_itinerary.deleted_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def hard_delete_itinerary(self, itinerary_id: uuid.UUID) -> bool:
        """Permanently delete an itinerary"""
        db_itinerary = self.get_itinerary_by_id(itinerary_id)
        if not db_itinerary:
            return False
        
        self.db.delete(db_itinerary)
        self.db.commit()
        return True
    
    def restore_itinerary(self, itinerary_id: uuid.UUID) -> Optional[Itinerary]:
        """Restore a soft-deleted itinerary"""
        db_itinerary = self.db.query(Itinerary).filter(
            Itinerary.itinerary_id == itinerary_id
        ).first()
        
        if not db_itinerary or db_itinerary.deleted_at is None:
            return None
        
        db_itinerary.deleted_at = None
        self.db.commit()
        self.db.refresh(db_itinerary)
        return db_itinerary
    
    def get_itinerary_stats(self, user_id: Optional[str] = None, session_id: Optional[uuid.UUID] = None) -> dict:
        """Get statistics for Auth0 user's or session's itineraries"""
        base_query = self.db.query(Itinerary).filter(Itinerary.deleted_at.is_(None))
        
        if user_id:
            base_query = base_query.filter(Itinerary.user_id == user_id)
        elif session_id:
            base_query = base_query.filter(Itinerary.session_id == session_id)
        else:
            return {"error": "Either user_id or session_id must be provided"}
        
        total = base_query.count()
        draft = base_query.filter(Itinerary.status == "draft").count()
        confirmed = base_query.filter(Itinerary.status == "confirmed").count()
        public = base_query.filter(Itinerary.visibility == "public").count()
        private = base_query.filter(Itinerary.visibility == "private").count()
        
        return {
            "total_itineraries": total,
            "draft_itineraries": draft,
            "confirmed_itineraries": confirmed,
            "public_itineraries": public,
            "private_itineraries": private
        }

    
    def initilize_agent(self, itinerary: Itinerary, thread_id: str):

        config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        initial_state = {
            "itinerary": itinerary.details_itinerary,
            "user_name": "Juan",
            "user_id": "user_123",
        }

        print(f"✅ PASO 1: A punto de invocar el agente para el thread_id: {thread_id}")

        try:
            itinerary_agent.invoke(initial_state, config=config)
        except Exception as e:
            print(f"❌ ERROR: La invocación del agente falló con una excepción: {e}")
            raise # Re-lanza la excepción para que FastAPI la maneje

        print("✅ PASO 2: La invocación del agente finalizó con éxito.")

        raw_state = itinerary_agent.get_state(config)
        state_dict = state_to_dict(raw_state)

        return state_dict     

    # ===== Propose changes (preview) =====
    def propose_itinerary_changes(self, itinerary_id: uuid.UUID, instruction: str) -> ItineraryDiffResponse | None:
        """Generate a proposed itinerary based on an instruction and compute a diff vs current.

        Returns an ItineraryDiffResponse or None if itinerary not found/invalid.
        """
        itinerary = self.get_itinerary_by_id(itinerary_id)
        if not itinerary or not itinerary.details_itinerary:
            return None

        # 1) Parse current itinerary to structured ViajeState
        try:
            current_state = ViajeState.model_validate(itinerary.details_itinerary)
        except Exception:
            # If current data doesn't match, abort gracefully
            return None

        # 2) Build a per-day activities list with stable IDs from current_state (heuristic id gen if absent)
        current_structured = self._build_structured_days_with_ids(current_state)

        # 3) Ask LLM to return ProposedTrip with stable ids
        model = ChatOpenAI(model="gpt-4o-mini")
        structured_llm = model.with_structured_output(ProposedTrip)

        system_prompt = (
            "Eres un asistente experto en ajustar itinerarios.\n"
            "Recibirás una lista por día de actividades con IDs estables.\n"
            "Debes devolver el mismo formato JSON exacto (days -> activities), respetando los IDs existentes cuando la actividad se mantiene o se modifica.\n"
            "Para nuevas actividades, genera un UUID v4 como id.\n"
            "REGLAS CRÍTICAS (DE CUMPLIMIENTO OBLIGATORIO):\n"
            "1) Integridad Absoluta del Texto: Si una actividad no cambia, su descripción debe copiarse EXACTAMENTE igual: sin añadir ni quitar ningún carácter (prohibido '}', '{', '},{'), sin cambiar puntuación/acentos/mayúsculas.\n"
            "2) Granularidad Significativa: Cada actividad debe ser una acción completa y autónoma; no dividas una misma acción en frases pequeñas.\n"
            "3) Texto limpio: Usa solo texto humano en 'name' y 'description' (sin artefactos JSON).\n"
            "No agregues explicaciones. Solo JSON válido."
        )

        user_content = {
            "current": current_structured,
            "instruction": instruction,
        }

        try:
            proposed_trip: ProposedTrip = structured_llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=str(user_content)),
            ])
            # Minimal validation: ensure list exists and each activity has id+description
            if not hasattr(proposed_trip, "days") or not isinstance(proposed_trip.days, list):
                raise ValueError("Invalid ProposedTrip: missing days")
            for d in proposed_trip.days:
                if d.day_number is None:
                    raise ValueError("Invalid ProposedTrip: day_number missing")
                for a in d.activities:
                    if not a.id or not a.name or not a.description:
                        raise ValueError("Invalid ProposedTrip: activity missing id/name/description")
                    # Sanitize any stray artifacts from LLM output defensively
                    desc = a.description
                    desc = desc.replace('},{', ', ').replace('} , {', ', ')
                    desc = desc.replace('[', '').replace(']', '').replace('{', '').replace('}', '')
                    a.description = re.sub(r"\s{2,}", " ", desc).strip()
        except Exception:
            # Safety rail fallback
            msg = "The AI assistant could not generate a valid suggestion at this time. Please try again later."
            return ItineraryDiffResponse(days=[], diff_results=[], summary=None, proposed_itinerary=None, error=msg)

        # 4) Compute a per-day diff using stable IDs
        diff = self._compute_diff_by_ids(current_structured, proposed_trip)
        # Keep diff_results alias in sync for fallback compatibility with FE
        diff.diff_results = diff.days
        # Log provenance
        try:
            self._log_change_proposal(itinerary.itinerary_id, instruction, diff.summary)
        except Exception:
            # non-fatal
            pass
        # We still need a full proposed_itinerary (ViajeState) for confirmation
        try:
            proposed_state: ViajeState = self._apply_structured_days_to_viaje(current_state, proposed_trip)
            diff.proposed_itinerary = proposed_state.model_dump()
        except Exception:
            # If transform fails, keep diff but omit proposed payload
            diff.proposed_itinerary = None
        return diff

    def _split_activities(self, actividades_text: str) -> list[str]:
        """Heuristic split of a day's 'actividades' string into individual items."""
        if not actividades_text:
            return []
        # Sanitize common stray artifacts first (defense-in-depth)
        cleaned = actividades_text.replace('},{', ', ').replace('} , {', ', ')
        cleaned = cleaned.replace('[', '').replace(']', '').replace('{', '').replace('}', '')
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()

        # Try splitting on strong sentence delimiters first to reduce over-splitting
        separators = ['. ', '; ', ' | ']
        parts = [cleaned]
        for sep in separators:
            new_parts = []
            for p in parts:
                new_parts.extend([x.strip() for x in p.split(sep)])
            parts = new_parts
        # Optional light split on comma, but only when it seems to join independent clauses (avoid breaking noun phrases)
        comma_split = []
        for p in parts:
            if len(p) > 80 and "," in p:
                comma_split.extend([x.strip() for x in p.split(",")])
            else:
                comma_split.append(p)

        # Remove empties and very short fillers; stitch lines that are too short into previous when likely fragments
        candidates = [p.strip(" -•\u2022\t\n\r") for p in comma_split]
        candidates = [p for p in candidates if p]

        items: list[str] = []
        for p in candidates:
            if items and (len(p) < 25 or not re.search(r"[a-zA-ZáéíóúñÁÉÍÓÚ]", p)):
                # Likely fragment: append to previous with comma
                items[-1] = (items[-1].rstrip(" .;,|") + ", " + p.lstrip(", ")).strip()
            else:
                items.append(p)
        return items

    def _compute_diff(self, current: ViajeState, proposed: ViajeState) -> ItineraryDiffResponse:
        # Build day -> activities mapping for current and proposed
        day_to_acts_current: dict[int, list[str]] = {}
        for destino in current.destinos:
            for dia in destino.dias_destino:
                day_to_acts_current[dia.posicion_dia] = self._split_activities(dia.actividades)

        day_to_acts_new: dict[int, list[str]] = {}
        for destino in proposed.destinos:
            for dia in destino.dias_destino:
                day_to_acts_new[dia.posicion_dia] = self._split_activities(dia.actividades)

        all_days = sorted(set(day_to_acts_current.keys()) | set(day_to_acts_new.keys()))
        day_diffs: list[DayDiff] = []

        added = deleted = modified = unchanged = 0
        for d in all_days:
            old_list = day_to_acts_current.get(d, [])
            new_list = day_to_acts_new.get(d, [])

            # Match activities with fuzzy similarity to detect modifications
            unmatched_new = set(range(len(new_list)))
            unmatched_old = set(range(len(old_list)))
            activity_entries: list[ActivityDiff] = []

            # First pass: pair similar activities as unchanged or modified
            for i_old, old_item in enumerate(old_list):
                best_j = None
                best_score = 0.0
                for j in list(unmatched_new):
                    new_item = new_list[j]
                    score = SequenceMatcher(None, old_item.lower(), new_item.lower()).ratio()
                    if score > best_score:
                        best_score = score
                        best_j = j
                if best_j is not None and best_score >= 0.8:
                    # Consider unchanged if almost identical
                    status = "unchanged" if best_score >= 0.97 else "modified"
                    activity_entries.append(ActivityDiff(id=None, name=new_list[best_j], status=status))
                    unmatched_new.remove(best_j)
                    unmatched_old.remove(i_old)
                    if status == "unchanged":
                        unchanged += 1
                    else:
                        modified += 1

            # Remaining old -> deleted
            for i_old in sorted(unmatched_old):
                activity_entries.append(ActivityDiff(id=None, name=old_list[i_old], status="deleted"))
                deleted += 1

            # Remaining new -> added
            for j in sorted(unmatched_new):
                activity_entries.append(ActivityDiff(id=None, name=new_list[j], status="added"))
                added += 1

            day_diffs.append(DayDiff(day_number=d, activities=activity_entries))

        summary = f"added: {added}, deleted: {deleted}, modified: {modified}, unchanged: {unchanged}"
        return ItineraryDiffResponse(days=day_diffs, summary=summary)

    def _build_structured_days_with_ids(self, current: ViajeState) -> dict:
        """Convert current ViajeState to per-day activities with stable IDs.
        Supports both legacy string 'actividades' and new structured list of objects.
        Generates deterministic IDs for each activity based on day/index.
        """
        days: List[Dict[str, Any]] = []
        for destino in current.destinos:
            for dia in destino.dias_destino:
                activities: List[Dict[str, Any]] = []
                if isinstance(dia.actividades, list):
                    # New structured schema
                    for idx, act in enumerate(dia.actividades):
                        nombre = getattr(act, "nombre", None)
                        if nombre is None and isinstance(act, dict):
                            nombre = act.get("nombre")
                        descripcion = getattr(act, "descripcion", None)
                        if descripcion is None and isinstance(act, dict):
                            descripcion = act.get("descripcion", "")
                        if not nombre:
                            # Derive a short title from description if missing
                            base = (descripcion or "").strip()
                            nombre = (base[:60] + ("…" if len(base) > 60 else "")) if base else "Actividad"
                        activities.append({
                            "id": f"day{dia.posicion_dia}-a{idx}",
                            "name": nombre,
                            "description": descripcion or "",
                        })
                else:
                    # Legacy free-text schema
                    activities_texts = self._split_activities(dia.actividades)
                    for idx, text in enumerate(activities_texts):
                        text = text.strip()
                        # Derive a short title as first clause/sentence up to ~60 chars
                        short = text.split(".")[0]
                        if len(short) > 60:
                            short = short[:60] + "…"
                        activities.append({
                            "id": f"day{dia.posicion_dia}-a{idx}",
                            "name": short or "Actividad",
                            "description": text,
                        })
                days.append({
                    "day_number": dia.posicion_dia,
                    "activities": activities,
                })
        # Merge duplicate day_number entries (in case multiple destinos share days)
        merged: Dict[int, List[Dict[str, Any]]] = {}
        for d in days:
            merged.setdefault(d["day_number"], []).extend(d["activities"])
        return {
            "days": [
                {"day_number": k, "activities": v}
                for k, v in sorted(merged.items(), key=lambda kv: kv[0])
            ]
        }

    def _compute_diff_by_ids(self, current_structured: dict, proposed_trip: ProposedTrip) -> ItineraryDiffResponse:
        day_diffs: List[DayDiff] = []
        added = deleted = modified = unchanged = 0

        current_days = {d["day_number"]: d["activities"] for d in current_structured.get("days", [])}
        proposed_days = {d.day_number: d.activities for d in proposed_trip.days}

        all_days = sorted(set(current_days.keys()) | set(proposed_days.keys()))
        for day in all_days:
            current_act = {a["id"]: a for a in current_days.get(day, [])}
            proposed_act = {a.id: a for a in proposed_days.get(day, [])}

            entries: List[ActivityDiff] = []

            # Unchanged/modified
            for aid, a in current_act.items():
                if aid in proposed_act:
                    new_name = proposed_act[aid].name
                    new_desc = proposed_act[aid].description
                    status = "unchanged" if (a.get("name") == new_name and a.get("description") == new_desc) else "modified"
                    if status == "unchanged":
                        unchanged += 1
                    else:
                        modified += 1
                    # Show combined title + description for diff name
                    entries.append(ActivityDiff(id=aid, name=f"{new_name}: {new_desc}", status=status))
                else:
                    # deleted
                    deleted += 1
                    entries.append(ActivityDiff(id=aid, name=f"{a.get('name','')}: {a.get('description','')}", status="deleted"))

            # Added
            for aid, a in proposed_act.items():
                if aid not in current_act:
                    added += 1
                    entries.append(ActivityDiff(id=aid, name=f"{a.name}: {a.description}", status="added"))

            day_diffs.append(DayDiff(day_number=day, activities=entries))

        summary = f"added: {added}, deleted: {deleted}, modified: {modified}, unchanged: {unchanged}"
        return ItineraryDiffResponse(days=day_diffs, summary=summary)

    def _apply_structured_days_to_viaje(self, current: ViajeState, proposed_trip: ProposedTrip) -> ViajeState:
        """Produce a new ViajeState by replacing per-day actividades with a structured list of objects."""
        # Build map day_number -> list of structured activities
        day_to_acts: Dict[int, List[Dict[str, Any]]] = {}
        for d in proposed_trip.days:
            acts: List[Dict[str, Any]] = []
            for a in d.activities:
                # Persist only nombre/descripcion in ViajeState; IDs are for diffing only
                acts.append({
                    "nombre": a.name,
                    "descripcion": a.description,
                })
            day_to_acts[d.day_number] = acts

        proposed_days_sorted = sorted(day_to_acts.keys())

        # Prepare a fast lookup of which global day_numbers currently exist
        existing_day_numbers: set[int] = set()
        for destino in current.destinos:
            for dia in destino.dias_destino:
                existing_day_numbers.add(dia.posicion_dia)

        # Clone current state deeply while applying replacements
        new_destinos = []
        for destino in current.destinos:
            new_dias = []
            for dia in destino.dias_destino:
                # Replace actividades when proposed has that day; otherwise keep existing
                new_struct = day_to_acts.get(dia.posicion_dia, None)
                if new_struct is None:
                    # If current is string schema (legacy), convert to structured list preserving content
                    if isinstance(dia.actividades, str):
                        texts = self._split_activities(dia.actividades)
                        acts_struct: List[Dict[str, Any]] = []
                        for idx, text in enumerate(texts):
                            text = text.strip()
                            short = text.split(".")[0]
                            if len(short) > 60:
                                short = short[:60] + "…"
                            acts_struct.append({
                                "nombre": short or "Actividad",
                                "descripcion": text,
                            })
                        new_dias.append(type(dia)(posicion_dia=dia.posicion_dia, actividades=acts_struct))
                    else:
                        # Already structured; keep as-is
                        new_dias.append(type(dia)(posicion_dia=dia.posicion_dia, actividades=dia.actividades))
                else:
                    new_dias.append(type(dia)(posicion_dia=dia.posicion_dia, actividades=new_struct))

            new_destinos.append(type(destino)(
                nombre_destino=destino.nombre_destino,
                cantidad_dias_en_destino=destino.cantidad_dias_en_destino,
                dias_destino=new_dias,
            ))

        # If there are proposed days not present in current, append them to the last destination
        missing_days = [d for d in proposed_days_sorted if d not in existing_day_numbers]
        if missing_days:
            # Choose a destination to receive the extra days: prefer the last one
            target_idx = len(new_destinos) - 1 if new_destinos else -1
            if target_idx >= 0:
                target_dest = new_destinos[target_idx]
                # Create DiaDestinoState entries for each missing day
                DiaDestinoStateCls = type(target_dest.dias_destino[0]) if target_dest.dias_destino else None
                for dnum in missing_days:
                    acts = day_to_acts.get(dnum, [])
                    if DiaDestinoStateCls is None:
                        # Fallback: construct using schema class from typing (import at top)
                        from state import DiaDestinoState as DiaCls
                        dia_obj = DiaCls(posicion_dia=dnum, actividades=acts)
                    else:
                        dia_obj = DiaDestinoStateCls(posicion_dia=dnum, actividades=acts)
                    target_dest.dias_destino.append(dia_obj)
                # Keep days sorted by posicion_dia
                target_dest.dias_destino = sorted(target_dest.dias_destino, key=lambda d: d.posicion_dia)
                # Update destination day count if it matches the semantics in current schema
                try:
                    target_dest.cantidad_dias_en_destino = len(target_dest.dias_destino)
                except Exception:
                    pass

        # Update overall trip day count to reflect proposed
        new_total_days = max(proposed_days_sorted) if proposed_days_sorted else current.cantidad_dias

        return type(current)(
            nombre_viaje=current.nombre_viaje,
            cantidad_dias=new_total_days,
            destino_general=current.destino_general,
            destinos=new_destinos,
        )

    def _log_change_proposal(self, itinerary_id: uuid.UUID, user_prompt: str, ai_response_summary: str | None):
        log = ItineraryChangeLog(
            itinerary_id=itinerary_id,
            user_prompt=user_prompt,
            ai_response_summary=ai_response_summary,
        )
        self.db.add(log)
        self.db.commit()

    def list_change_logs(self, itinerary_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[ItineraryChangeLog]:
        return (
            self.db.query(ItineraryChangeLog)
            .filter(ItineraryChangeLog.itinerary_id == itinerary_id)
            .order_by(ItineraryChangeLog.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def confirm_itinerary_changes(self, itinerary_id: uuid.UUID, proposed_itinerary: dict) -> Optional[Itinerary]:
        """Persist a proposed itinerary state into the database."""
        itinerary = self.get_itinerary_by_id(itinerary_id)
        if not itinerary:
            return None

        try:
            validated = ViajeState.model_validate(proposed_itinerary)
        except Exception:
            return None

        update = ItineraryUpdate(
            details_itinerary=validated.model_dump(),
            trip_name=validated.nombre_viaje,
            duration_days=validated.cantidad_dias,
        )
        return self.update_itinerary(itinerary_id, update)


    def send_agent_message(self, itinerary_id: uuid.UUID, thread_id: str, message: str):
        config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        raw_state = itinerary_agent.get_state(config)
        state_dict = state_to_dict(raw_state)
        if not is_valid_thread_state(state_dict):
            return False

        is_hil_mode, hil_message, state_values = detect_hil_mode(itinerary_agent, config)

        if is_hil_mode:
            itinerary_agent.invoke(Command(resume={"messages": message}), config=config)

            itinerary = self.get_itinerary_by_id(itinerary_id)

            agent_state = self.get_agent_state(thread_id)

            itinerary_update = ItineraryUpdate(
                details_itinerary=agent_state[0]["itinerary"],
                trip_name=agent_state[0]["itinerary"]["nombre_viaje"],
                duration_days=agent_state[0]["itinerary"]["cantidad_dias"],
                slug=itinerary.slug,
                destination=itinerary.destination,
                start_date=itinerary.start_date,
                travelers_count=itinerary.travelers_count,
                budget=itinerary.budget,
                trip_type=itinerary.trip_type,
                tags=itinerary.tags,
                notes=itinerary.notes,
                visibility=itinerary.visibility,
                status=itinerary.status,
            )

            self.update_itinerary(itinerary_id, itinerary_update)

            return agent_state
  
        itinerary_agent.invoke({"messages": message}, config=config)

        return self.get_agent_state(thread_id)


    def get_agent_state(self, thread_id: str):
        config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        raw_state = itinerary_agent.get_state(config)
        state_dict = state_to_dict(raw_state)
        if not is_valid_thread_state(state_dict):
            return False

        return state_dict


# Convenience functions for dependency injection
def get_itinerary_service(db: Session) -> ItineraryService:
    """Factory function to create ItineraryService instance"""
    return ItineraryService(db)
