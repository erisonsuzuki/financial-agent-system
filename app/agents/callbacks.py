from typing import Any, Optional

from langchain.callbacks.stdout import StdOutCallbackHandler


class SafeStdOutCallbackHandler(StdOutCallbackHandler):
    """
    StdOut callback that tolerates agents which don't provide serialized metadata.
    """

    def on_chain_start(
        self, serialized: Optional[dict[str, Any]], inputs: dict[str, Any], **kwargs: Any
    ) -> None:
        if "name" in kwargs:
            name = kwargs["name"]
        elif serialized:
            name = serialized.get("name", serialized.get("id", ["<unknown>"])[-1])
        else:
            name = "<unknown>"
        print(f"\n\n\033[1m> Entering new {name} chain...\033[0m")
