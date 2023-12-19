import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from openai import OpenAI

client = OpenAI()


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
    def __call__(self, prompt: list[dict]) -> dict:
        ...


@dataclass
class ChatGPT(Completer):
    temperature: float = 0.7
    model: str = 'gpt-3.5-turbo'

    def __call__(self, messages: list[dict[str, str]]) -> dict:
        completion = client.chat.completions.create(model=self.model, messages=messages, temperature=self.temperature)
        content = completion.choices[0].message.content # type: ignore
        print(content)
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
    return completer(Prompt(format_instructions=format_instructions, system_prompt=system_prompt, user_prompt=prompt).messages)


def create_initial_data(completer: Completer, intention: str, example_tags: list[str], example_link_types: list[tuple[str, str]]) -> dict:
    format_instructions = '{"tags": ["tag_1", "tag_2", ...], "link_types": [["link_type_1", "link_type_1_reverse"], ["link_type_2", "link_type_2_reverse"], ...]}'
    messages = [
        {
        "role": "system",
        "content": f"You are a helpful assistant. Your task is to provide a list of tags and link types to someone who is beginning to use an app where they create a knowledge graph of their ideas and those of their friends. In this app, they can use tags to group ideas, and use links to connect ideas. They can do the same for references and memos.\n\nThe user will provide a description of their intention and interests, and you will provide some initial relevant tags and link types.\n\nHere is a list of default tags to use if they do not provide enough information to customize their tags: {example_tags}. Return 8-15 tags. In general, the tags should refer to the major themes and concepts in the content of interest.\n\nEach link type has names for both forward and reverse directions. If they do not provide enough information, here is a list of default link types: {example_link_types}. Return 5-10 link types.\n\nAlways return your answer in JSON format, like so: {format_instructions}. Return only the JSON, no extra characters."
        },
        {
        "role": "user",
        "content": "I want to use this app to collect inspiring buddhist passages, study and develop knowledge, and prepare talks."
        },
        {
        "role": "assistant",
        "content": '{"tags": ["wisdom", "love", "generosity", "right action", "right view", "right intention", "right speech",  "right livelihood", "right mindfulness", "right effort", "right concentration"], "link_types": [["Supports", "Supported by"], ["Elaboration of", "Elaborated by"], ["Inspiration for", "Inspired by"], ["Summary for", "Summarized by"], ["Related Question", "Question about"], ["Counterargument against", "Countered by"]]}'
        },
        {
        "role": "user",
        "content": "I want to use this app to collect news articles."
        },
        {
        "role": "assistant",
        "content": '{"tags": ["world news", "politics", "business", "technology", "sports", "entertainment", "science", "health"], "link_types": [["Supports", "Supported by"], ["Evidence for", "Supporting Evidence"], ["Takeaway", "Takeaway for"], ["Summary for", "Summarized by"], ["Related Question", "Question about"], ["Counterargument against", "Countered by"]]}'
        },
        {
        "role": "user",
        "content": intention
        }
    ]
    return completer(messages)



def get_tags(completer: Completer, contents: list[str], existing_tags: list[str]) -> list[list[str]]:
    format_instructions = '{"tags": {"0": ["text_0_tag_1", "text_0_tag_2", ...], "1": ["text_1_tag_1", "text_1_tag_2", ...], ...]}'
    system_prompt = f"""You are a helpful assistant who provides tags for texts. You are given a list of texts, and you return a dictionary of lists of tags, one list for each text. The key for each list is the index of the text in the provided list.

For each text, Create tags that address the intention of each text and its major themes. Strike a good balance between general and specific, creating keywords that will be relevant for other texts, both in the list and in general. Do not simply copy the terms from the text.

You have a list of existing tags. If an existing tag applies to the text, return it as one of the tags you provide. You may also create additional keywords that highlight aspects of the text that are not covered by the list of existing tags. Here are the existing tags: {[str(t) for t in existing_tags]}

Give 3-7 tags per text. Do not give more than 7 tags for a single text.

Return a list of tags for EACH text, in the same order the texts are provided."""
    prompt = Prompt(format_instructions=format_instructions, system_prompt=system_prompt, user_prompt=str(contents))
    out = completer(prompt.messages)
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
    return completer(prompt.messages)['ideas']