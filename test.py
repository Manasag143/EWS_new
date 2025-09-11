"Write a python code to hit an api using a request body and print the response"
import requests


def hit_api(url, request_body):
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.post(url, json=request_body, headers=headers, verify=False)

    if response.status_code == 200:
        print("Response:", response.json())
    else:
        print(f"Error: {response.status_code} - {response.text}")

# Example usage
if __name__ == "__main__":
    api_url = "http://localhost:8085/genai/ewsect/"  # Replace with your API URL
    #api_url = "https://gateway-ratings-dev.crisil.com/ratingsewsai/genai/ewsect"
    request_body = {
        "processId": "2c1f0a9e-c822-487f-8d99-032554e90ce7",
        "requestedBy": "1014094",
        "companyCode": "",
        "docName": "",
        "docPath": {
            "ECT": "genai_summarization_input/sample_ect_test.pdf",
            "MF": "genai_summarization_input/ect_test.xlsx"
        },
        "use_case": "ECT",
        "callBackURL": "https://gateway-ratings-dev.crisil.com/ratgenai/api/documents/callback/save-response"
    }
    hit_api(api_url, request_body)
