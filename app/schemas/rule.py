from pydantic import BaseModel, Field


class RuleSchema(BaseModel):
    name: str
    description: str
    example_bad: str = ""
    example_good: str = ""
    technologies: list[str] = Field(default_factory=list)
