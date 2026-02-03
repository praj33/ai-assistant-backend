# Windows Adapter for Assistant Core v3

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

### Embed Request
```json
{
  "texts": ["string"]
}
```

### Decision Hub Request
```json
{
  "input_text": "string",
  "platform": "windows",
  "device_context": "desktop"
}
```

## Auth Flow
1. Obtain token from `/auth/login` (external auth service)
2. Include in header: `Authorization: Bearer <token>`
3. Token refresh at `/auth/refresh`

## Example Call (C#)
```csharp
using System.Net.Http;
using System.Text;
using Newtonsoft.Json;

var client = new HttpClient();
client.DefaultRequestHeaders.Authorization = new AuthenticationHeaderValue("Bearer", token);

var content = new StringContent(JsonConvert.SerializeObject(new { texts = new[] { "Hello world" } }), Encoding.UTF8, "application/json");
var response = await client.PostAsync("https://api.assistantcore.com/api/embed", content);
var result = await response.Content.ReadAsStringAsync();