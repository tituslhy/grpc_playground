from sqlmodel import SQLModel, Field, create_engine, Session

class Todo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    task: str
    
engine = create_engine("sqlite:///todos.db", echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)

if __name__ == "__main__":
    init_db()