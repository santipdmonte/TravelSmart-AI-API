from docling.document_converter import DocumentConverter

source = "document_analyzer/pdf_example.pdf"  # PDF path or URL
converter = DocumentConverter()
result = converter.convert(source)
print(result.document.export_to_markdown())  # output: "### Docling Technical Report[...]"