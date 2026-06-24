# LangChain Tools

- Define LangChain tool arguments in the function signature with `Annotated[...]` instead of `args_schema`. (This matches the repo's tool pattern and avoids older compatibility issues.)
