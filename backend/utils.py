import os
from dotenv import load_dotenv
from langchain.tools import BaseTool
from langchain.agents import AgentType, initialize_agent
from langchain.llms import OllamaLLM  # Import OllamaLLM
from database.operations import search_materials, search_recipes, get_recipe_with_steps

load_dotenv()

MODEL_NAME = os.getenv("MODEL_NAME")
SERVER_URL = os.getenv("SERVER_URL")  

MODEL_NAME = "your_model_name_here"  # 定義模型名稱
llm = OllamaLLM(
    model=MODEL_NAME,   #  model名稱
    base_url=SERVER_URL  # 修正變數名稱
)

class SearchMaterialsTool(BaseTool):
    name = "search_materials"
    description = "搜尋材料資訊，輸入關鍵字"
    
    def _run(self, keyword: str):
        results = search_materials(keyword)
        if results.empty:
            return "找不到相關材料"
        return results.to_dict('records')

class SearchRecipesTool(BaseTool):
    name = "search_recipes"
    description = "搜尋配方資訊，輸入關鍵字"
    
    def _run(self, keyword: str):
        results = search_recipes(keyword)
        if results.empty:
            return "找不到相關配方"
        return results.to_dict('records')

class GetRecipeDetailTool(BaseTool):
    name = "get_recipe_detail"
    description = "取得配方詳細資訊，輸入配方ID"
    
    def _run(self, recipe_id: str):
        recipe = get_recipe_with_steps(recipe_id)
        if not recipe:
            return "找不到該配方"
        return recipe

# 在 LangChain 中使用這些工具
tools = [SearchMaterialsTool(), SearchRecipesTool(), GetRecipeDetailTool()]
agent = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True)