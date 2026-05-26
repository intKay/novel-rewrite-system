"""用户自由文本需求的数据结构。"""

from pydantic import BaseModel, ConfigDict, Field


class StoryRequirement(BaseModel):
    """小说改写需求的结构化表示。"""

    model_config = ConfigDict(extra="forbid")

    raw_text: str = Field(default="", description="原始用户自由文本需求")
    theme: str | None = Field(default=None, description="主题")
    worldview: str | None = Field(default=None, description="世界观")
    protagonist: str | None = Field(default=None, description="主角设定")
    supporting_characters: str | None = Field(default=None, description="配角设定")
    character_relationships: str | None = Field(default=None, description="人物关系")
    plot_direction: str | None = Field(default=None, description="情节方向")
    style_preferences: str | None = Field(default=None, description="风格偏好")
    forbidden_content: list[str] = Field(default_factory=list, description="禁止内容")
    required_plot_points: list[str] = Field(default_factory=list, description="必须出现的情节")
    ending_preference: str | None = Field(default=None, description="结局倾向")

    @classmethod
    def from_text(cls, raw_text: str) -> "StoryRequirement":
        """从用户自由文本创建需求对象。

        第一版只保留原始文本，不进行模型解析或规则抽取。
        """

        return cls(raw_text=raw_text)
