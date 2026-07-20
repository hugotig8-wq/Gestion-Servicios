from pathlib import Path

class PromptBuilder:

    def __init__(

        self,

        max_characters: int = 8000

    ):

        self.max_characters = max_characters

    def build(

        self,

        file_path: Path,

        source_code: str

    ) -> str:

        source_code = self._truncate(

            source_code

        )

        return f"""
You are an expert software engineer specialized in:

- Python
- Machine Learning
- MLOps

Analyze the following source code.

Return ONLY valid Markdown.

For every recommendation include:

1. Severity (LOW, MEDIUM, HIGH)
2. Category
3. Explanation
4. Why it is a problem
5. Suggested improvement
6. Corrected code if applicable
7. Return the response in Json
8. Implementation-estimated time

File:

{file_path}

Source code:

```text
{source_code}
"""

    def build_summary(

        self,

        recommendations: list[str]
    ) -> str:

        joined = "\n".join(

            recommendations

        )

        return f"""
You are an expert software architect.

You have received multiple code review reports.

Create a single consolidated report.

Requirements:

1. Group similar recommendations.
2. Remove duplicated suggestions.
3. Prioritize the most critical issues.
4. Identify recurring architectural problems.
5. Produce an action plan ordered by priority.
6. Return the response in valid Markdown.
7. Return response in Json.

Code review reports:

{joined}
"""

    def build_test(
        self, 
        funcion, 
        lenguaje)-> str:
            return f"""
        Generate comprehensive test cases to this function, {lenguaje}:
        
        ```{lenguaje}
        {funcion}
        ```
        
        Create tests to:
        1. Normal cases
        2. Edge cases
        3. Error handling
        4. Input validation
        
        Use frameworks by language:
        - JS: Jest
        - Python: pytest
        
        Response only test code.
        """
        
