from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI
import xml.etree.ElementTree as ET
import re
import os
from ..models import AgentState

load_dotenv()

# Initialize LLM
llm = AzureChatOpenAI(
    api_version="2024-10-21",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    temperature=0.1  # Lower temperature for more consistent code generation
)

class VectorGraphicsAgent:
    def __init__(self):
        self.format_generators = {
            "svg": self.generate_svg_code,
            "eps": self.generate_eps_code,
            "pdf": self.generate_pdf_code
        }
        
    def generate_vector_graphics_node(self, state: AgentState) -> AgentState:
        """Main vector graphics generation node with format selection."""
        print(f"---GENERATING {state.vector_format.upper()} VECTOR GRAPHICS---")
        
        state.generation_attempts += 1
        
        # Select appropriate generator based on format
        if state.vector_format in self.format_generators:
            generator = self.format_generators[state.vector_format]
            state = generator(state)
        else:
            state.validation_errors.append(f"Unsupported format: {state.vector_format}")
            return state
            
        # Validate the generated code
        state = self.validate_vector_code(state)
        
        return state
    
    def generate_svg_code(self, state: AgentState) -> AgentState:
        """Enhanced SVG generation with style and complexity considerations."""
        
        # Create enhanced prompt based on user preferences
        system_prompt = self.create_svg_system_prompt(state.style, state.complexity, state.color_scheme)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "{prompt}")
        ]).format(prompt=state.prompt)
        
        try:
            response = llm.invoke(prompt)
            state.svg_code = self.clean_svg_response(response.content)
            state.vector_code = state.svg_code
            state.format_specific_code["svg"] = state.svg_code
            
            # Add generation metadata
            state.generation_metadata.update({
                "format": "svg",
                "style": state.style,
                "complexity": state.complexity,
                "color_scheme": state.color_scheme
            })
            
        except Exception as e:
            state.validation_errors.append(f"SVG generation error: {str(e)}")
            
        return state
    
    def generate_eps_code(self, state: AgentState) -> AgentState:
        """Generate EPS (Encapsulated PostScript) code."""
        
        system_prompt = """You are an expert at creating EPS (Encapsulated PostScript) vector graphics code. 
        Generate clean, valid EPS code that creates the requested vector graphic. 
        Start with proper EPS headers (%!PS-Adobe-3.0 EPSF-3.0) and include bounding box information.
        Use PostScript drawing commands like moveto, lineto, curveto, fill, stroke, etc.
        Keep the code clean and well-structured."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "Create EPS code for: {prompt}")
        ]).format(prompt=state.prompt)
        
        try:
            response = llm.invoke(prompt)
            eps_code = self.clean_eps_response(response.content)
            state.vector_code = eps_code
            state.format_specific_code["eps"] = eps_code
            
            state.generation_metadata.update({
                "format": "eps",
                "style": state.style
            })
            
        except Exception as e:
            state.validation_errors.append(f"EPS generation error: {str(e)}")
            
        return state
    
    def generate_pdf_code(self, state: AgentState) -> AgentState:
        """Generate PDF vector graphics using reportlab or similar approach."""
        
        system_prompt = """You are an expert at creating Python code that generates PDF vector graphics using reportlab.
        Generate clean Python code that uses reportlab to create vector graphics in PDF format.
        Include proper imports, canvas setup, and drawing commands.
        Use reportlab's graphics capabilities like drawString, line, rect, circle, etc."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "Create reportlab Python code to generate PDF vector graphics for: {prompt}")
        ]).format(prompt=state.prompt)
        
        try:
            response = llm.invoke(prompt)
            pdf_code = self.clean_code_response(response.content)
            state.vector_code = pdf_code
            state.format_specific_code["pdf"] = pdf_code
            
            state.generation_metadata.update({
                "format": "pdf",
                "library": "reportlab"
            })
            
        except Exception as e:
            state.validation_errors.append(f"PDF generation error: {str(e)}")
            
        return state
    
    def create_svg_system_prompt(self, style: str, complexity: str, color_scheme: str) -> str:
        """Create enhanced system prompt based on style preferences."""
        
        base_prompt = """You are an expert at creating beautiful, modern, and valid SVG code. 
        Generate a single, complete, standalone SVG that is properly formatted and valid.
        Do not include markdown, backticks, or explanatory text."""
        
        style_instructions = {
            "modern": "Use clean lines, geometric shapes, and contemporary design principles.",
            "minimalist": "Use simple shapes, minimal colors, and lots of white space.",
            "detailed": "Include intricate details, patterns, and complex compositions.",
            "artistic": "Be creative with flowing curves, artistic elements, and expressive forms."
        }
        
        complexity_instructions = {
            "simple": "Create a simple design with 3-5 basic shapes and minimal detail.",
            "medium": "Create a moderately complex design with 6-15 elements and some detail.",
            "complex": "Create a detailed design with many elements, patterns, and intricate details."
        }
        
        color_instructions = {
            "monochrome": "Use only black, white, and shades of gray.",
            "vibrant": "Use bright, saturated colors that pop and create energy.",
            "pastel": "Use soft, muted colors with light tones.",
            "default": "Use appropriate colors that enhance the design."
        }
        
        enhanced_prompt = f"""{base_prompt}
        
        Style: {style_instructions.get(style, "Use a balanced, professional approach.")}
        Complexity: {complexity_instructions.get(complexity, "Create a well-balanced design.")}
        Colors: {color_instructions.get(color_scheme, "Use colors that work well together.")}
        
        Ensure the SVG is valid, well-structured, and visually appealing."""
        
        return enhanced_prompt
    
    def validate_vector_code(self, state: AgentState) -> AgentState:
        """Validate generated vector code based on format."""
        
        if state.vector_format == "svg" and state.svg_code:
            state.is_valid = self.validate_svg(state.svg_code)
        elif state.vector_format == "eps" and state.vector_code:
            state.is_valid = self.validate_eps(state.vector_code)
        elif state.vector_format == "pdf" and state.vector_code:
            state.is_valid = self.validate_pdf_code(state.vector_code)
        
        return state
    
    def validate_svg(self, svg_code: str) -> bool:
        """Validate SVG code structure."""
        try:
            # Basic XML validation
            ET.fromstring(svg_code)
            
            # Check for required SVG elements
            if not svg_code.strip().startswith('<svg'):
                self.add_validation_error("SVG must start with <svg> tag")
                return False
                
            if '</svg>' not in svg_code:
                self.add_validation_error("SVG must end with </svg> tag")
                return False
                
            return True
            
        except ET.ParseError as e:
            self.add_validation_error(f"Invalid XML structure: {str(e)}")
            return False
    
    def validate_eps(self, eps_code: str) -> bool:
        """Basic EPS validation."""
        if not eps_code.startswith('%!PS-Adobe'):
            return False
        if '%%BoundingBox:' not in eps_code:
            return False
        return True
    
    def validate_pdf_code(self, pdf_code: str) -> bool:
        """Basic PDF code validation."""
        required_imports = ['reportlab', 'canvas']
        return any(imp in pdf_code for imp in required_imports)
    
    def clean_svg_response(self, response: str) -> str:
        """Clean and extract SVG code from LLM response."""
        # Remove markdown code blocks
        response = re.sub(r'```\n?', '', response)
        
        # Extract SVG content
        svg_match = re.search(r'<svg.*?</svg>', response, re.DOTALL | re.IGNORECASE)
        if svg_match:
            return svg_match.group(0)
        
        return response.strip()
    
    def clean_eps_response(self, response: str) -> str:
        """Clean EPS response."""
        response = re.sub(r'```\n?', '', response)
        return response.strip()
    
    def clean_code_response(self, response: str) -> str:
        """Clean code response."""
        response = re.sub(r'```\n?', '', response)
        return response.strip()

    def refinement_node(self, state: AgentState) -> AgentState:
        """Refine the generated vector graphics if validation fails."""
        
        if state.is_valid or state.generation_attempts >= state.max_attempts:
            return state
            
        print(f"---REFINING {state.vector_format.upper()} (Attempt {state.generation_attempts})---")
        
        # Create refinement prompt
        errors = "; ".join(state.validation_errors)
        refinement_prompt = f"""The previous {state.vector_format.upper()} code had these issues: {errors}
        Please fix these issues and generate a corrected version.
        Original request: {state.prompt}"""
        
        # Clear previous errors
        state.validation_errors = []
        
        # Re-generate with refinement
        return self.generate_vector_graphics_node(state)

def create_vector_graphics_graph() -> StateGraph:
    """Create the enhanced vector graphics generation graph."""
    
    agent = VectorGraphicsAgent()
    
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("generator", agent.generate_vector_graphics_node)
    workflow.add_node("validator", agent.validate_vector_code)
    workflow.add_node("refiner", agent.refinement_node)
    
    # Set entry point
    workflow.set_entry_point("generator")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "generator",
        lambda state: "end" if state.is_valid else ("refiner" if state.generation_attempts < state.max_attempts else "end"),
        {
            "refiner": "refiner",
            "end": END
        }
    )
    
    workflow.add_conditional_edges(
        "refiner",
        lambda state: "end" if state.is_valid or state.generation_attempts >= state.max_attempts else "refiner",
        {
            "refiner": "refiner",
            "end": END
        }
    )
    
    return workflow.compile()

# Usage example
def generate_vector_graphics(
    prompt: str,
    vector_format: str = "svg",
    style: str = "modern",
    complexity: str = "medium",
    color_scheme: str = "default"
) -> AgentState:
    """Main function to generate vector graphics."""
    
    # Initialize state
    initial_state = AgentState(
        prompt=prompt,
        vector_format=vector_format,
        style=style,
        complexity=complexity,
        color_scheme=color_scheme
    )
    
    # Create and run the graph
    graph = create_vector_graphics_graph()
    final_state = graph.invoke(initial_state)
    
    return final_state

# Example usage
if __name__ == "__main__":
    result = generate_vector_graphics(
        prompt="Create a modern logo for a tech startup with geometric shapes",
        vector_format="svg",
        style="modern",
        complexity="medium",
        color_scheme="vibrant"
    )
    
    print(f"Generated {result.vector_format.upper()}:")
    print(result.vector_code)
    print(f"Valid: {result.is_valid}")
    if result.validation_errors:
        print(f"Errors: {result.validation_errors}")
