from typing import Dict, List, Tuple

import chainlit as cl


class AnswerFormatter:
    def _format_video_elem(self, source: Dict) -> cl.Text | cl.Video:
        """Generate the appropriate Chainlit element based on the source of the video."""
        if "echo360" in source['url']:
            iframe_html = f"<html><iframe src={source['url']} width='100%' height='500px' frameborder='0'></iframe></html>"
            return cl.Text(name=source['title'], content=iframe_html, display="side")
        elif "youtube" in source['url']:
            return cl.Video(name=source['title'], url=source['url'], display="side")
        else:
            raise ValueError(f"Unsupported video source: {source['url']}")

    def format_citations(self, citations: Dict[str, Dict]) -> Tuple[str, List]:
        """Formats citations and prepares video elements so it can be embedded."""
        formatted_citations = ""
        video_elements = []
        if citations:
            for id, source in citations.items():
                if source['content_type'] == 'video_transcript':
                    video_elements.append(self._format_video_elem(source))
                    formatted_citations += f"{id}. {source['title']}\n"
                else:
                    formatted_citations += f"{id}. [{source['title']}]({source['url']})\n"
        return formatted_citations, video_elements

    async def send_msg(self, answer: str, citations: Dict[str, Dict]) -> cl.Message:
        """
        Format the answer with citations as a ChainLit message.
        """
        formatted_citations, video_elements = self.format_citations(citations)
        answer_and_citations = f"{answer}\n\n**Sources:**\n{formatted_citations}"
        await cl.Message(content=answer_and_citations, elements=video_elements).send()
