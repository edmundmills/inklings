import json
from dataclasses import dataclass
from typing import Optional

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

    def complete(self, temperature: float = 0) -> dict:
        completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=self.messages, temperature=temperature)
        content = completion.choices[0].message.content # type: ignore
        return json.loads(content)


def get_tags_and_title(text: str, title: Optional[str], existing_tags: list[str]) -> dict:
    format_instructions = '{"tags": ["tag_1", "tag_2", ...], "title": "generated_title"}'
    system_prompt = f"""You are a helpful assistant who provides tags, given a text. Create tags that address the intention of the text and its major themes. Strike a good balance between general and specific, creating keywords that will be relevant for other texts. Do not simply copy the terms from the text.

You have a list of existing tags. If an existing tag applies to the text, return it as one of the tags you provide. You may also create additional keywords that highlight aspects of the text that are not covered by the list of existing tags. Here are the existing tags: {existing_tags}

Give 3-7 tags. Do not give more than 7 tags.

You also provide an appropriate title, if the existing title is None."""
    prompt = f"<h1>{title}</h1>\n{text}"
    return Prompt(format_instructions=format_instructions, system_prompt=system_prompt, user_prompt=prompt).complete()


def create_inklings(text: str, title: str, existing_tags: list[str]) -> list[dict]:
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
    ideas = Prompt(format_instructions=format_instructions, system_prompt=system_prompt, user_prompt=f"<h1>{title}</h1>\n{text}").complete()['ideas']
    return [{"content": idea, "tags": get_tags_and_title(idea, title=None, existing_tags=existing_tags)['tags']} for idea in ideas]
