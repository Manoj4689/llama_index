# AdobeExtractReader Loader

```bash
pip install llama-index-readers-file pdfservices-sdk
```

This loader extracts text from a local PDF using the pdfservices-sdk library. If metadata=True is passed to the load_data function, documents will include metadata like page numbers, file path, and total pages. You can also add extra context via the extra_info parameter.

## Usage
Pass the file path (string or Path) and Adobe credentials to extract content as Document objects for use with LlamaIndex.

```python
from pathlib import Path

from llama_index.readers.file import AdobeExtractReader

loader = AdobeExtractReader(client_id='ENTER YOUR ADOBE CLIENT ID', client_secret='ENTER YOUR ADOBE CLIENT SECRET')
documents = loader.load_data(file_path=Path("./article.pdf"), metadata=True)
```

This loader is designed to be used as a way to load data into [LlamaIndex](https://github.com/run-llama/llama_index/).
