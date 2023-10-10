import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

import openai


@dataclass
class Prompt:
    format_instructions: str
    system_prompt: str
    user_prompt: str

    @property
    def full_system_prompt(self):
        return f"{self.system_prompt}\n\nAlways return your answer in JSON format, like so: {self.format_instructions}. Return only the JSON, no extra characters."

    @property
    def messages(self) -> list[dict]:
        return [{"role": "system", "content": self.full_system_prompt}, {"role": "user", "content": self.user_prompt}]



class Completer(ABC):
    @abstractmethod
    def __call__(self, prompt: Prompt) -> dict:
        ...


@dataclass
class ChatGPT(Completer):
    temperature: float = 0.7
    model: str = 'gpt-3.5-turbo'

    def __call__(self, prompt: Prompt) -> dict:
        completion = openai.ChatCompletion.create(model=self.model, messages=prompt.messages, temperature=self.temperature)
        content = completion.choices[0].message.content # type: ignore
        return json.loads(content)



def get_generated_metadata(completer: Completer, text: str, title: Optional[str], existing_tags: list[str]) -> dict:
    format_instructions = '{"tags": ["tag_1", "tag_2", ...], "title": "generated_title", "summary": "summary_text"}'
    system_prompt = f"""You are a helpful assistant who provides tags, a title, and a short summary, given a text.

Create tags that address the intention of the text and its major themes. Strike a good balance between general and specific, creating keywords that will be relevant for other texts. Do not simply copy the terms from the text.

You have a list of existing tags. If an existing tag applies to the text, return it as one of the tags you provide. You may also create additional keywords that highlight aspects of the text that are not covered by the list of existing tags. Here are the existing tags: {[str(t) for t in existing_tags]}

Give 3-7 tags. Do not give more than 7 tags.

You also provide an appropriate title, if the existing title is None.

Give a short summary. The summary should be a short paragraph, of no more than three sentences."""
    prompt = f"<h1>{title}</h1>\n{text[:5000]}"
    return completer(Prompt(format_instructions=format_instructions, system_prompt=system_prompt, user_prompt=prompt))


def get_tags(completer: Completer, contents: list[str], existing_tags: list[str]) -> list[list[str]]:
    format_instructions = '{"tags": {"0": ["text_0_tag_1", "text_0_tag_2", ...], "1": ["text_1_tag_1", "text_1_tag_2", ...], ...]}'
    system_prompt = f"""You are a helpful assistant who provides tags for texts. You are given a list of texts, and you return a dictionary of lists of tags, one list for each text. The key for each list is the index of the text in the provided list.

For each text, Create tags that address the intention of each text and its major themes. Strike a good balance between general and specific, creating keywords that will be relevant for other texts, both in the list and in general. Do not simply copy the terms from the text.

You have a list of existing tags. If an existing tag applies to the text, return it as one of the tags you provide. You may also create additional keywords that highlight aspects of the text that are not covered by the list of existing tags. Here are the existing tags: {[str(t) for t in existing_tags]}

Give 3-7 tags per text. Do not give more than 7 tags for a single text.

Return a list of tags for EACH text, in the same order the texts are provided."""
    prompt = Prompt(format_instructions=format_instructions, system_prompt=system_prompt, user_prompt=str(contents))
    out = completer(prompt)
    return [out['tags'][str(i)] for i in range(len(out))]


def create_inklings(completer: Completer, text: str, title: str) -> list[dict]:
    format_instructions = '{"ideas": ["idea_1", "idea_2", ...]"}'
    system_prompt = f"""You are a helpful assistant who distills the key ideas from a given text.

Given a text, return a comprehensive list of the ideas expressed in the text, which may include:
- Ideas expressed directly
- Underlying principles
- Ideas that connect the various threads in the text

When expressing the ideas, keep in mind:
- Each idea should be expressed in a clear, compelling, and insightful way.
- Each may be a single sentence to a short paragraph.
- The ideas do not need to be copied from the text verbatim. Try to give them in the voice of the person who wrote the text.
- Each idea should be able to stand on its own as an insightful quote or tweet.  Their meaning should be understood without seeing the main text or any of the other ideas."""
    prompt = Prompt(format_instructions=format_instructions, system_prompt=system_prompt, user_prompt=f"<h1>{title}</h1>\n{text}")
    return completer(prompt)['ideas']