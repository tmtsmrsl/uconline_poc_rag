import datetime
import re
from typing import Dict, List
from urllib.parse import urlparse, urlunparse


def _add_timestamp_to_url(url, start_time):
    """
    Add a timestamp query parameter to the video URL.
    """
    # Parse the URL to list because the ParseResult tuple is immutable
    url_parts = list(urlparse(url))

    # Add the timestamp query parameter
    query = f"t={int(start_time)}"
    
    # the query parameter is the 5th element in the list
    # If there's already a query string, append the new parameter
    if url_parts[4]:  
        url_parts[4] += "&" + query
    # Otherwise, create a new query string
    else:
        url_parts[4] = query

    # Reconstruct the URL
    return urlunparse(url_parts)

def _add_timestamps_to_title(title, block_ids, extra_end_time=15):
    """Modify the video title with timestamps. 
    block_ids is a sorted list of start timestamps in seconds.
    The extra_end_time should be adjusted based on index_metadata_freq arg on TranscriptDocProcessor.
    """
    start_time = int(block_ids[0])
    end_time = int(block_ids[-1]) + extra_end_time
    
    # convert start time and end time to hh:mm:ss format
    start_time = str(datetime.timedelta(seconds=start_time))
    end_time = str(datetime.timedelta(seconds=end_time))
    return f"{title} ({(start_time)}-{end_time})"

def process_video_citation(citation):
    """Process video citation and format with timestamps."""
    block_ids = sorted(citation['block_ids'])
    earliest_time = block_ids[0]
    new_citation = {
        'final_url': _add_timestamp_to_url(citation['url'], earliest_time),
        'title': _add_timestamps_to_title(citation['title'], block_ids),
        'old_citation_ids': citation['old_citation_ids'],
        'block_ids': block_ids,
        'content_type': citation['content_type']
    }
    return new_citation

class CitationFormatter:
    @staticmethod
    def _deduplicate_consecutive_citations(text: str) -> str:
    # Find groups of consecutive citations and deduplicate them
        def replace_consecutive(match):
            citations = re.findall(r'\[(\d+)\]', match.group(0))
            unique_citations = []
            for citation in citations:
                # Only remove duplicates within this consecutive group
                if citation not in unique_citations:
                    unique_citations.append(citation)
            return ''.join(f'[{citation}]' for citation in unique_citations)
        
        # Pattern to match one or more consecutive citations
        pattern = r'(?:\[\d+\])+' 
        return re.sub(pattern, replace_consecutive, text)
    
    def format_final_answer(self, answer: str, source_metadata: List[Dict]) -> Dict:
        def replace_citation(match, citation_mapping):
            old_id = int(match.group(1)) 
            # Get the new_citation_id or keep the old one if not found
            new_id = citation_mapping.get(old_id, None)
            if new_id:  
                return f"[{new_id}]"
            else:
                raise ValueError(f"Could not find the old citation id {old_id} in citation_mapping")
        
        # extract the citation ids from the answer
        citation_pattern = re.compile(r"\[(\d+)\]")
        citation_ids = citation_pattern.findall(answer)
        citation_ids = set([int(id) for id in citation_ids])

        # find the source for each citation
        citation_data = []

        unique_urls = set()
        # merge source_metadata with the same url
        # note that the source_metadata is already sorted by the order of source_id (which will now be the old_citation_id)
        for source in source_metadata:
            matching_ids = set(source['source_ids']).intersection(citation_ids)
            if matching_ids:
                if source['content_type'] == 'video_transcript':
                    # Modified: group video splits using merge_threshold
                    splits = [s for s in source['source_splits'] if s['source_id'] in matching_ids]
                    splits.sort(key=lambda s: s['block_id'])
                    merge_threshold = 60  # seconds threshold for merging splits
                    current_group = []
                    for split in splits:
                        if not current_group:
                            current_group.append(split)
                        else:
                            if split['block_id'] - current_group[-1]['block_id'] <= merge_threshold:
                                current_group.append(split)
                            else:
                                citation = {
                                    "url": source['url'], 
                                    "title": source['title'],
                                    "old_citation_ids": [s['source_id'] for s in current_group], 
                                    "block_ids": [s['block_id'] for s in current_group],
                                    "content_type": source['content_type']
                                }
                                citation_data.append(citation)
                                current_group = [split]
                    if current_group:
                        citation = {
                            "url": source['url'], 
                            "title": source['title'],
                            "old_citation_ids": [s['source_id'] for s in current_group], 
                            "block_ids": [s['block_id'] for s in current_group],
                            "content_type": source['content_type']
                        }
                        citation_data.append(citation)
                else:
                    if source['url'] not in unique_urls:
                        unique_urls.add(source['url'])
                        citation = {"url": source['url'], 
                                    "title": source['title'],
                                    "old_citation_ids": [], 
                                    "block_ids": [],
                                    "content_type": source['content_type']}
                        for source_split in source['source_splits']:
                            if source_split['source_id'] in matching_ids:
                                citation['old_citation_ids'].append(source_split['source_id'])
                                # this block id is already sorted by their char start index in the source text
                                citation['block_ids'].append(source_split['block_id'])
                        citation_data.append(citation)
                    else:
                        citation = next((c for c in citation_data if c['url'] == source['url']), None)
                        for source_split in source['source_splits']:
                            if source_split['source_id'] in matching_ids:
                                citation['old_citation_ids'].append(source_split['source_id'])
                                citation['block_ids'].append(source_split['block_id'])
        
        print(citation_data)
        new_citation_data = []
        for citation in citation_data:        
            if citation['content_type'] == 'video_transcript':
                new_citation_data.append(process_video_citation(citation))
            elif citation['content_type'] == 'html_content':
                citation['final_url'] = citation['url'] + "/block/" + ",".join(citation['block_ids'])
                new_citation_data.append(citation)
                
        print(new_citation_data)
        # process the final citation url and id
        new_citation_id = 1
        for citation in new_citation_data:
            citation['new_citation_id'] = new_citation_id
            new_citation_id += 1

        # Create a mapping of old_citation_id to new_citation_id
        citation_mapping = {}
        for citation in new_citation_data:
            for old_citation_id in citation['old_citation_ids']:
                citation_mapping[old_citation_id] = citation['new_citation_id']
        
        final_answer = re.sub(r'\[(\d+)\]', lambda match: replace_citation(match, citation_mapping), answer)
                
        final_citation = {}
        for citation in new_citation_data:
            final_citation[citation['new_citation_id']] = {"url": citation['final_url'], "title": citation['title'], "content_type": citation['content_type']}
        
        # deduplicate the final citation
        final_answer = self._deduplicate_consecutive_citations(final_answer)
        
        return {"content": final_answer, "citation": final_citation}