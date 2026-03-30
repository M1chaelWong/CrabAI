from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.storage.models import Conversation, Message, File, Memory


class ConversationRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> Conversation:
        conv = Conversation(**kwargs)
        self.session.add(conv)
        await self.session.commit()
        await self.session.refresh(conv)
        return conv

    async def get(self, conv_id: str) -> Conversation | None:
        return await self.session.get(Conversation, conv_id)

    async def get_with_messages(self, conv_id: str) -> Conversation | None:
        stmt = (
            select(Conversation)
            .where(Conversation.id == conv_id)
            .options(selectinload(Conversation.messages))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Conversation]:
        stmt = select(Conversation).order_by(Conversation.updated_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(self, conv_id: str, **kwargs) -> Conversation | None:
        conv = await self.get(conv_id)
        if not conv:
            return None
        for key, value in kwargs.items():
            setattr(conv, key, value)
        await self.session.commit()
        await self.session.refresh(conv)
        return conv

    async def delete(self, conv_id: str) -> bool:
        conv = await self.get(conv_id)
        if not conv:
            return False
        await self.session.delete(conv)
        await self.session.commit()
        return True


class MessageRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> Message:
        msg = Message(**kwargs)
        self.session.add(msg)
        await self.session.commit()
        await self.session.refresh(msg)
        return msg

    async def get(self, msg_id: str) -> Message | None:
        return await self.session.get(Message, msg_id)

    async def list_by_conversation(self, conv_id: str) -> list[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conv_id)
            .order_by(Message.sequence_num)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_from_sequence(self, conv_id: str, from_seq: int) -> None:
        stmt = (
            delete(Message)
            .where(Message.conversation_id == conv_id)
            .where(Message.sequence_num >= from_seq)
        )
        await self.session.execute(stmt)
        await self.session.commit()


class FileRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> File:
        f = File(**kwargs)
        self.session.add(f)
        await self.session.commit()
        await self.session.refresh(f)
        return f

    async def get(self, file_id: str) -> File | None:
        return await self.session.get(File, file_id)

    async def list_by_conversation(self, conv_id: str) -> list[File]:
        stmt = select(File).where(File.conversation_id == conv_id).order_by(File.created_at)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class MemoryRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert(self, key: str, content: str, source: str | None = None) -> Memory:
        stmt = select(Memory).where(Memory.key == key)
        result = await self.session.execute(stmt)
        mem = result.scalar_one_or_none()
        if mem:
            mem.content = content
            if source is not None:
                mem.source = source
        else:
            mem = Memory(key=key, content=content, source=source)
            self.session.add(mem)
        await self.session.commit()
        await self.session.refresh(mem)
        return mem

    async def get(self, key: str) -> Memory | None:
        stmt = select(Memory).where(Memory.key == key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Memory]:
        stmt = select(Memory).order_by(Memory.key)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete(self, key: str) -> bool:
        mem = await self.get(key)
        if not mem:
            return False
        await self.session.delete(mem)
        await self.session.commit()
        return True
