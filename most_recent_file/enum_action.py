import argparse
import enum
from typing import Any, Callable, Iterable, Optional, Sequence, Tuple, TypeVar, Union

E = TypeVar("E", bound=enum.Enum)


def enum_action(e: E):
    class EnumAction(argparse.Action):
        def __init__(
            self,
            option_strings: Sequence[str],
            dest: str,
            nargs: Optional[Union[int, str]] = None,
            const: Optional[E] = None,
            default: Union[E, str, None] = None,
            type: Optional[
                Union[
                    Callable[[str], E],
                    Callable[[str], E],
                    argparse.FileType,
                ]
            ] = None,
            choices: Optional[Iterable[E]] = None,
            required: bool = None,
            help: Optional[str] = None,
            metavar: Optional[Union[str, Tuple[str, ...]]] = None,
        ) -> None:
            if isinstance(default, enum.Enum) and help is not None:
                help = f"{help} (default: {default.name.lower()})"
            super().__init__(
                option_strings,
                dest,
                nargs=nargs,
                const=const,
                default=default,
                type=type,
                choices=[variant.name.lower() for variant in e],
                required=required,
                help=help,
                metavar=metavar,
            )

        def __call__(
            self,
            parser: argparse.ArgumentParser,
            namespace: argparse.Namespace,
            values: Union[str, Sequence[Any], None],
            option_string: Optional[str],
        ) -> None:
            setattr(namespace, self.dest, E[values.upper()])

    return EnumAction
