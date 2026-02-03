# Web Adapter for Assistant Core v3

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

### Respond Request
```json
{
  "query": "string",
  "context": {},
  "model": "uniguru"
}
```

### Decision Hub Request
```json
{
  "input_text": "string",
  "platform": "web",
  "device_context": "desktop"
}
```

## Auth Flow
1. Obtain token from `/auth/login` (external auth service)
2. Include in header: `Authorization: Bearer <token>`
3. Token refresh at `/auth/refresh`

## Example Call (JavaScript)
```javascript
const response = await fetch('https://api.assistantcore.com/api/respond', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'Hello',
    context: {}
  })
});

const data = await response.json();
console.log(data);