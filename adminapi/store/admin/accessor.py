from hashlib import sha256
from typing import Optional

from sqlalchemy import select, insert
from sqlalchemy.engine import ChunkedIteratorResult

from adminapi.admin.admin_dataclasses import Admin
from adminapi.base.base_accessor import BaseAccessor
from adminapi.admin.models import AdminModel


class AdminAccessor(BaseAccessor):
    async def get_by_login(self, login: str) -> Optional[Admin]:
        select_query = select(AdminModel).where(AdminModel.login == login)
        async with self.app.database.session() as session:
            res = await session.execute(select_query)
        wrapped_data: AdminModel = res.scalar()
        if wrapped_data:
            return Admin(login=wrapped_data.login, password=wrapped_data.password)

    async def create_admin(self, login: str, password: str):
        admin = AdminModel(
            login=login,
            password=sha256(password.encode()).hexdigest()
        )
        async with self.app.database.session() as session:
            session.add(admin)
            await session.commit()
            await session.refresh(admin)
        return Admin(login=admin.login, password=admin.password)
