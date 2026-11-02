
def test_upload_csv(client, sample_csv_bytes):

    response = client.post(
            "/upload",
            files={
                "file": (
                    "sample_data.csv",
                    sample_csv_bytes,
                    "text/csv"
                )
            }
        )
    assert response.status_code == 200

    data = response.json()
    assert data.get("rows") == 6
    assert data.get("columns") == 2

    dataset_info = data.get("id")
    assert isinstance(dataset_info, int) and dataset_info > 0


def test_process_and_retrieve(client, uploaded_dataset_id, processing_body):

    process_response = client.post(f"/datasets/{uploaded_dataset_id}/process",
        json=processing_body)
    assert process_response.status_code == 200

    process_data = process_response.json()
    assert process_data.get("validation_rows_removed") == 1
    assert process_data.get("cleaning_report", {}).get("rows_before") == 5
    assert process_data.get("cleaning_report", {}).get("rows_after") == 3

    
    retrieve_response = client.get(f"/datasets/{uploaded_dataset_id}")
    assert retrieve_response.status_code == 200

    retrieved_data = retrieve_response.json()
    assert retrieved_data.get("total_rows") == 3

    records = retrieved_data.get("records", [])
    record_data= {record.get("student_id"): record.get("score") for record in records}
    assert record_data[1] == 80
    assert record_data[2] == 90
    assert record_data[5] == 85


def test_retrieve_missing_dataset(client):
    missing_id = 12345
    response = client.get(f"/datasets/{missing_id}")

    assert response.status_code == 404