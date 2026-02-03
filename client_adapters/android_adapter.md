# Android Adapter for Assistant Core v3

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

### Intent Request
```json
{
  "text": "string",
  "model": "uniguru"
}
```

### Decision Hub Request
```json
{
  "input_text": "string",
  "platform": "android",
  "device_context": "mobile"
}
```

## Auth Flow
1. Obtain token from `/auth/login` (external auth service)
2. Include in header: `Authorization: Bearer <token>`
3. Token refresh at `/auth/refresh`

## Example Call (Kotlin)
```kotlin
val url = "https://api.assistantcore.com/api/intent"
val request = Request.Builder()
    .url(url)
    .post(RequestBody.create(MediaType.parse("application/json"), """{"text": "Hello"}"""))
    .addHeader("Authorization", "Bearer $token")
    .build()

OkHttpClient().newCall(request).enqueue(object : Callback {
    override fun onResponse(call: Call, response: Response) {
        // Handle response
    }
})