from pathlib import Path
from typing import Dict, List, Optional, Union
import json

from llama_index.core.readers.base import BaseReader
from llama_index.core.schema import Document

class AdobeExtractReader(BaseReader):
    """Read PDF files using Adobe PDF Services SDK."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        extract_images: bool = False,
    ):
        try:
            from adobe.pdfservices.operation.auth.service_principal_credentials import ServicePrincipalCredentials
            from adobe.pdfservices.operation.pdf_services import PDFServices
            from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_pdf_params import ExtractPDFParams
            from adobe.pdfservices.operation.pdfjobs.params.extract_pdf.extract_element_type import ExtractElementType
        except ImportError:
            raise ImportError(
                "`pdfservices` package not found. Please install it with `pip install pdfservices-sdk`."
            )

        credentials = ServicePrincipalCredentials(client_id=client_id, client_secret=client_secret)
        self.pdf_services = PDFServices(credentials=credentials)
        self.extract_pdf_params = ExtractPDFParams(elements_to_extract=[ExtractElementType.TEXT])
        self.extract_images = extract_images

    def load_data(
        self,
        file_path: Union[Path, str],
        metadata: bool = True,
        extra_info: Optional[Dict] = None,
    ) -> List[Document]:
        """Loads list of documents from a PDF file.

        Args:
            file_path (Union[Path, str]): Path to the PDF file.
            metadata (bool, optional): Whether to include metadata. Defaults to True.
            extra_info (Optional[Dict], optional): Additional information to include. Defaults to None.

        Returns:
            List[Document]: List of documents containing extracted text and metadata.
        """
        if not isinstance(file_path, (str, Path)):
            raise TypeError("file_path must be a string or Path.")

        file_path = str(file_path)  # Ensure file_path is a string
        self._upload_pdf(file_path)
        self._submit_job()
        self._fetch_results_json()

        return self._convert_output_to_documents(metadata=metadata, extra_info=extra_info)

    def _upload_pdf(self, file_path: str):
        try:
            from adobe.pdfservices.operation.pdf_services_media_type import PDFServicesMediaType
        except ImportError:
            raise ImportError(
                "`pdfservices` package not found. Please install it with `pip install pdfservices-sdk`."
            )

        with open(file_path, "rb") as file:
            input_stream = file.read()
        self.input_asset = self.pdf_services.upload(input_stream=input_stream, mime_type=PDFServicesMediaType.PDF)

    def _submit_job(self):
        try:
            from adobe.pdfservices.operation.pdfjobs.jobs.extract_pdf_job import ExtractPDFJob
        except ImportError:
            raise ImportError(
                "`pdfservices` package not found. Please install it with `pip install pdfservices-sdk`."
            )

        extract_pdf_job = ExtractPDFJob(input_asset=self.input_asset, extract_pdf_params=self.extract_pdf_params)
        self.location = self.pdf_services.submit(extract_pdf_job)

    def _fetch_results_json(self):
        import zipfile
        import io

        try:
            from adobe.pdfservices.operation.pdfjobs.result.extract_pdf_result import ExtractPDFResult
            from adobe.pdfservices.operation.io.cloud_asset import CloudAsset
            from adobe.pdfservices.operation.io.stream_asset import StreamAsset
        except ImportError:
            raise ImportError(
                "`pdfservices` package not found. Please install it with `pip install pdfservices-sdk`."
            )

        pdf_services_response = self.pdf_services.get_job_result(self.location, ExtractPDFResult)
        result_asset: CloudAsset = pdf_services_response.get_result().get_resource()
        stream_asset: StreamAsset = self.pdf_services.get_content(result_asset)

        zip_file_bytes = io.BytesIO(stream_asset.get_input_stream())
        self.extract_output = None
        with zipfile.ZipFile(zip_file_bytes, "r") as z:
            for file_name in z.namelist():
                if file_name == "structuredData.json":
                    with z.open(file_name) as f:
                        self.extract_output = json.load(f)

    def _convert_output_to_documents(
        self, metadata: bool = True, extra_info: Optional[Dict] = None
    ) -> List[Document]:
        text_per_page = {}
        for element in self.extract_output["elements"]:
            if "Text" in element:
                text_in_element = element["Text"]
                page_number = element["Page"]
                if page_number not in text_per_page:
                    text_per_page[page_number] = ""
                text_per_page[page_number] += text_in_element + "\n"

        documents = []
        for page_number, text in text_per_page.items():
            doc_metadata = extra_info.copy() if extra_info else {}
            if metadata:
                doc_metadata.update({"page_number": page_number})

            documents.append(Document(text=text, extra_info=doc_metadata))

        return documents
