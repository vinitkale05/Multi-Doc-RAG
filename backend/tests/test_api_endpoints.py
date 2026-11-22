import asyncio
import httpx
from app.main import app
from app.core.database import init_db


def test_health_endpoints():
    async def _run():
        await init_db()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/v1/health")
            assert resp.status_code == 200
            assert resp.json()["status"] == "healthy"

            resp_ready = await client.get("/api/v1/ready")
            assert resp_ready.status_code == 200
            assert resp_ready.json()["status"] == "ready"

    asyncio.run(_run())


def test_auth_registration_and_login():
    async def _run():
        await init_db()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            reg_payload = {
                "email": "vinit.kale@mitadt.edu.in",
                "password": "SecurePassword123!",
                "tenant_name": "MIT School of Computing",
                "role": "admin"
            }
            resp = await client.post("/api/v1/auth/register", json=reg_payload)
            assert resp.status_code == 201
            data = resp.json()
            assert "access_token" in data
            assert "refresh_token" in data

            login_payload = {
                "email": "vinit.kale@mitadt.edu.in",
                "password": "SecurePassword123!"
            }
            login_resp = await client.post("/api/v1/auth/login", json=login_payload)
            assert login_resp.status_code == 200
            assert "access_token" in login_resp.json()

    asyncio.run(_run())
