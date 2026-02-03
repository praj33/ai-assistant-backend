# iOS Adapter for Assistant Core v3

## API Endpoints
- Base URL: `https://api.assistantcore.com/api`
- All endpoints require Bearer token authentication

## JSON Schemas

### Authentication
```json
{
  "token": "string",
  "expires_in": 3600
}
```

### Summarize Request
```json
{
  "text": "string",
  "max_length": 100,
  "model": "uniguru"
}
```

### Decision Hub Request
```json
{
  "input_text": "string",
  "platform": "ios",
  "device_context": "mobile"
}
```

## Auth Flow
1. Obtain token from `/auth/login` (external auth service)
2. Include in header: `Authorization: Bearer <token>`
3. Token refresh at `/auth/refresh`

## Example Call (Swift)
```swift
let url = URL(string: "https://api.assistantcore.com/api/summarize")!
var request = URLRequest(url: url)
request.httpMethod = "POST"
request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
request.setValue("application/json", forHTTPHeaderField: "Content-Type")

let body = ["text": "Long text to summarize", "max_length": 50]
request.httpBody = try JSONSerialization.data(withJSONObject: body)

URLSession.shared.dataTask(with: request) { data, response, error in
    // Handle response
}.resume()