from typing import Dict, List, Union

type Atome = Union[str, int, float, bool, List[Serializable], List[Atome], None]
type Serializable = Union[Dict[str, Serializable], Atome]
