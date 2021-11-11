from dataclasses import dataclass
from typing import Union


@dataclass
class Suggestion:
    """
    Dataclass for inline suggestions. 
    Will become HelpEntry in future and replace current command_description etc.

    icon: Icon in InlineQueryArticle
    title: Title in InlineQueryArticle ("Maybe try {Title}")
    example_command: Example command usage
    """
    icon: Union[str, None]
    title: str
    example_command: str
