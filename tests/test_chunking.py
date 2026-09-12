from belgeiz.chunking import chunk_page, clean_text


def test_clean_text_preserves_useful_line_breaks():
    assert clean_text(" Başlık  \n\n\n Satır   bir \n Satır iki ") == (
        "Başlık\n\nSatır bir\nSatır iki"
    )


def test_chunk_page_preserves_source_metadata_and_overlap():
    text = " ".join(f"kelime{i}" for i in range(25))
    chunks = chunk_page(text, "rapor.pdf", 3, "pdf-text", max_words=10, overlap_words=2)

    assert len(chunks) == 3
    assert all(chunk.page == 3 for chunk in chunks)
    assert all(chunk.document_name == "rapor.pdf" for chunk in chunks)
    assert chunks[0].text.split()[-2:] == chunks[1].text.split()[:2]
    assert len({chunk.id for chunk in chunks}) == len(chunks)

