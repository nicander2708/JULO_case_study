import jwt
from datetime import datetime, timedelta, timezone

def generateJWT(
    customer_xid: str, jwt_secret: str = "secret", expires_in: int = 120
) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "customer_xid": customer_xid,
    }
    token = jwt.encode(payload, jwt_secret, algorithm="HS256")
    return token

def decodeJWT(token: str, jwt_secret: str = "secret") -> dict:
    try:
        decoded_token = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        return decoded_token
    except Exception as err:
        raise err
