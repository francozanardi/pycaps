from dataclasses import dataclass, field
from typing import List, Optional, Set, TYPE_CHECKING
from .types import ElementState

if TYPE_CHECKING:
    from movielite import GraphicClip, AudioClip

@dataclass(frozen=True)
class Tag:
    name: str

    def to_dict(self) -> dict:
        return {"name": self.name}
    
    @staticmethod
    def from_dict(data: dict) -> 'Tag':
        return Tag(name=data["name"])

@dataclass
class TimeFragment:
    start: float = 0
    end: float = 0

    def to_dict(self) -> dict:
        return {"start": self.start, "end": self.end}

    @staticmethod
    def from_dict(data: dict) -> 'TimeFragment':
        return TimeFragment(start=data["start"], end=data["end"])

@dataclass
class Size:
    width: int = 0
    height: int = 0

    def to_dict(self) -> dict:
        return {"width": self.width, "height": self.height}

    @staticmethod
    def from_dict(data: dict) -> 'Size':
        return Size(width=data["width"], height=data["height"])

@dataclass
class Position:
    x: int = 0
    y: int = 0

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y}

    @staticmethod
    def from_dict(data: dict) -> 'Position':
        return Position(x=data["x"], y=data["y"])

@dataclass
class ElementLayout:
    position: Position = field(default_factory=Position)
    size: Size = field(default_factory=Size)

    def to_dict(self) -> dict:
        return {"position": self.position.to_dict(), "size": self.size.to_dict()}
    
    @staticmethod
    def from_dict(data: dict) -> 'ElementLayout':
        return ElementLayout(position=Position.from_dict(data["position"]), size=Size.from_dict(data["size"]))

    def get_center(self) -> Position:
        return Position(x=self.position.x + self.size.width / 2, y=self.position.y + self.size.height / 2)


# TODO: I should handle caching for methods like get_words.
#  It should be refreshed automatically when a child is added or removed.

@dataclass
class WordClip:
    _parent: Optional['Word'] = None
    states: List[ElementState] = field(default_factory=list)
    media_clip: Optional['GraphicClip'] = None
    layout: ElementLayout = field(default_factory=ElementLayout)

    def to_dict(self) -> dict:
        return {"states": [state.value for state in self.states], "layout": self.layout.to_dict()}

    @staticmethod
    def from_dict(data: dict) -> 'WordClip':
        return WordClip(states=[ElementState(state) for state in data["states"]], layout=ElementLayout.from_dict(data["layout"]))

    def has_state(self, state: ElementState) -> bool:
        return state in self.states

    def get_word(self) -> 'Word':
        return self._parent

    def get_line(self) -> 'Line':
        return self._parent.get_line()
    
    def get_segment(self) -> 'Segment':
        return self._parent.get_segment()
    
    def get_document(self) -> 'Document':
        return self._parent.get_document()

@dataclass
class Word:
    _parent: Optional['Line'] = None
    _clips: 'ElementContainer[WordClip]' = field(init=False)
    text: str = ""
    semantic_tags: Set[Tag] = field(default_factory=set)
    structure_tags: Set[Tag] = field(default_factory=set)
    # IMPORTANT: it saves the maximum width/height of their clips (the word slot size)
    #            same with the position: it's the x,y of the word slot
    max_layout: ElementLayout = field(default_factory=ElementLayout)
    time: TimeFragment = field(default_factory=TimeFragment)

    def __post_init__(self):
        self._clips = ElementContainer(self)

    def to_dict(self) -> dict:
        return {
            "clips": [clip.to_dict() for clip in self.clips],
            "text": self.text,
            "semantic_tags": [tag.to_dict() for tag in self.semantic_tags],
            "structure_tags": [tag.to_dict() for tag in self.structure_tags],
            "max_layout": self.max_layout.to_dict(), "time": self.time.to_dict()
        }

    @staticmethod
    def from_dict(data: dict) -> 'Word':
        word = Word(
            text=data["text"],
            semantic_tags=set([Tag.from_dict(tag) for tag in data["semantic_tags"]]),
            structure_tags=set([Tag.from_dict(tag) for tag in data["structure_tags"]]),
            max_layout=ElementLayout.from_dict(data["max_layout"]),
            time=TimeFragment.from_dict(data["time"])
        )
        word._clips.set_all([WordClip.from_dict(clip) for clip in data["clips"]])
        return word

    @property
    def clips(self) -> 'ElementContainer[WordClip]':
        return self._clips
    
    def get_tags(self) -> Set[Tag]:
        return self.structure_tags | self.semantic_tags

    def get_media_clips(self) -> List['GraphicClip']:
        return [clip.media_clip for clip in self.clips]

    def get_line(self) -> 'Line':
        return self._parent

    def get_segment(self) -> 'Segment':
        return self._parent.get_segment()
    
    def get_document(self) -> 'Document':
        return self._parent.get_document()
    
    def get_all_tags_in_document(self) -> Set[Tag]:
        return self.structure_tags | self.semantic_tags | self.get_line().structure_tags | self.get_segment().structure_tags

@dataclass
class Line:
    _parent: Optional['Segment'] = None
    _words: 'ElementContainer[Word]' = field(init=False)
    structure_tags: Set[Tag] = field(default_factory=set)
    max_layout: ElementLayout = field(default_factory=ElementLayout)
    time: TimeFragment = field(default_factory=TimeFragment) # TODO: We could calculate it using the words (same for segment)

    def __post_init__(self):
        self._words = ElementContainer(self)

    def to_dict(self) -> dict:
        return {
            "words": [word.to_dict() for word in self.words],
            "structure_tags": [tag.to_dict() for tag in self.structure_tags],
            "max_layout": self.max_layout.to_dict(), "time": self.time.to_dict()
        }

    @staticmethod
    def from_dict(data: dict) -> 'Line':
        line = Line(
            structure_tags=set([Tag.from_dict(tag) for tag in data["structure_tags"]]),
            max_layout=ElementLayout.from_dict(data["max_layout"]),
            time=TimeFragment.from_dict(data["time"])
        )
        line._words.set_all([Word.from_dict(word) for word in data["words"]])
        return line

    @property
    def words(self) -> 'ElementContainer[Word]':
        return self._words

    def get_text(self) -> str:
        return ' '.join([word.text for word in self.words])
    
    def get_tags(self) -> Set[Tag]:
        return self.structure_tags

    def get_media_clips(self) -> List['GraphicClip']:
        return [clip for word in self.words for clip in word.get_media_clips()]
    
    def get_word_clips(self) -> List[WordClip]:
        return [clip for word in self.words for clip in word.clips]
    
    def get_segment(self) -> 'Segment':
        return self._parent
    
    def get_document(self) -> 'Document':
        return self._parent.get_document()

@dataclass
class Segment:
    _parent: Optional['Document'] = None
    _lines: 'ElementContainer[Line]' = field(init=False)
    structure_tags: Set[Tag] = field(default_factory=set)
    max_layout: ElementLayout = field(default_factory=ElementLayout)
    time: TimeFragment = field(default_factory=TimeFragment)

    def __post_init__(self):
        self._lines = ElementContainer(self)

    def to_dict(self) -> dict:
        return {
            "lines": [line.to_dict() for line in self.lines],
            "structure_tags": [tag.to_dict() for tag in self.structure_tags],
            "max_layout": self.max_layout.to_dict(),
            "time": self.time.to_dict()
        }

    @staticmethod
    def from_dict(data: dict) -> 'Segment':
        segment = Segment(
            structure_tags=set([Tag.from_dict(tag) for tag in data["structure_tags"]]),
            max_layout=ElementLayout.from_dict(data["max_layout"]),
            time=TimeFragment.from_dict(data["time"])
        )
        segment._lines.set_all([Line.from_dict(line) for line in data["lines"]])
        return segment

    @property
    def lines(self) -> 'ElementContainer[Line]':
        return self._lines

    def get_text(self) -> str:
        return ' '.join([line.get_text() for line in self.lines])
    
    def get_tags(self) -> Set[Tag]:
        return self.structure_tags
    
    def get_media_clips(self) -> List['GraphicClip']:
        return [clip for line in self.lines for clip in line.get_media_clips()]
    
    def get_word_clips(self) -> List[WordClip]:
        return [clip for line in self.lines for clip in line.get_word_clips()]
    
    def get_words(self) -> List[Word]:
        return [word for line in self.lines for word in line.words]
    
    def get_document(self) -> 'Document':
        return self._parent

@dataclass
class Document:
    _segments: 'ElementContainer[Segment]' = field(init=False)
    sfxs: List['AudioClip'] = field(default_factory=list)

    def __post_init__(self):
        self._segments = ElementContainer(self)

    def to_dict(self) -> dict:
        return {"segments": [segment.to_dict() for segment in self.segments]}

    @staticmethod
    def from_dict(data: dict) -> 'Document':
        document = Document()
        document._segments.set_all([Segment.from_dict(segment) for segment in data["segments"]])
        return document

    @property
    def segments(self) -> 'ElementContainer[Segment]':
        return self._segments

    def get_media_clips(self) -> List['GraphicClip']:
        return [clip for segment in self.segments for clip in segment.get_media_clips()]

    def get_word_clips(self) -> List[WordClip]:
        return [clip for segment in self.segments for clip in segment.get_word_clips()]
    
    def get_words(self) -> List[Word]:
        return [word for segment in self.segments for word in segment.get_words()]
    
    def get_lines(self) -> List[Line]:
        return [line for segment in self.segments for line in segment.lines]
    
    def get_text(self) -> str:
        return ' '.join([segment.get_text() for segment in self.segments])

from .element_container import ElementContainer