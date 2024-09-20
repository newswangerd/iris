/ -> serves react app
/login -> returns a JWT token
/users -> get and create users
/users/<name> -> get and delete user
/users/<name>/gen_token -> return JWT for a user
/ws -> websocket

Directory structure:
```
users
  <user_id>/
    settings.json
    <uuid>.wav
    <uuid>.json
translated/
  <date>.txt
```

JWT
```
{
  iss: user_id,
  lang: language code,
  role: user|admin,
}
```

Websocket

first message -> Client type (speaker/listener)
  if listener
    <- list of translated messsages for the day
    <- Additional messages as they come in
  if speaker
    -> audio stream
    <- transcribed message
    -> accept/reject
