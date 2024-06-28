<?php
require 'vendor/autoload.php';

use GuzzleHttp\Client;
use GuzzleHttp\Exception\GuzzleException;

// Function to perform face comparison
function performFaceComparison() {
    // Hard-coded variables for testing
    $apiEndpoint = 'http://your-fastapi-server.com/face-comparison';
    $apiKey = 'your-api-key-here';
    $image1Path = 'photos/man.jpg';
    $image2Path = 'photos/lady.jpg';

    // Create a new Guzzle client
    $client = new Client();

    try {
        $response = $client->request('POST', $apiEndpoint, [
            'multipart' => [
                [
                    'name'     => 'image1',
                    'contents' => fopen($image1Path, 'r'),
                    'filename' => 'image1.jpg'
                ],
                [
                    'name'     => 'image2',
                    'contents' => fopen($image2Path, 'r'),
                    'filename' => 'image2.jpg'
                ]
            ]
        ]);

        $statusCode = $response->getStatusCode();
        $body = json_decode($response->getBody()->getContents(), true);

        return [
            'status' => $statusCode,
            'data' => $body
        ];

    } catch (GuzzleException $e) {
        return [
            'status' => 500,
            'error' => $e->getMessage()
        ];
    }
}

// Perform face comparison on page load
$result = performFaceComparison();
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Face Comparison Results</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .container {
            max-width: 800px;
            margin: auto;
            background: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
        }
        #results {
            margin-top: 20px;
        }
        .error {
            color: red;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Face Comparison Results</h1>
        <div id="results">Loading...</div>
    </div>

    <script>
        // Function to update the results on the page
        function updateResults(data) {
            const resultsDiv = document.getElementById('results');
            if (data.status === 200) {
                resultsDiv.innerHTML = `
                    <h2>Similarity Score: ${data.data.similarity_score}</h2>
                    <h3>Analysis:</h3>
                    <p>${data.data.description}</p>
                `;
            } else {
                resultsDiv.innerHTML = `<p class="error">Error: ${data.error || 'Unknown error occurred'}</p>`;
            }
        }

        // Update results on page load
        document.addEventListener('DOMContentLoaded', () => {
            updateResults(<?php echo json_encode($result); ?>);
        });
    </script>
</body>
</html>