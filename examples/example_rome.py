import os
import sys
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm import LLM
from core.rome_model_editor import ROMEModelEditor, EditRequest

load_dotenv()

def demonstrate_rome_knowledge_editing():
    """
    ROMEを使用した知識編集機能のデモンストレーション
    
    このデモでは、LLMの内部知識を編集し、その効果を検証します。
    1. 初期状態での知識を確認
    2. ROMEを使用して知識を編集
    3. 編集後の知識を確認
    4. 複数の編集を適用して累積効果を確認
    """
    print("=== ROME Knowledge Editing Demonstration ===")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable not set")
        return
    
    llm = LLM(
        api_key=api_key,
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    )
    
    rome_editor = ROMEModelEditor()
    
    llm.set_rome_model_editor(rome_editor)
    
    print("\n--- Test 1: Editing Knowledge about Japan's Capital ---")
    
    prompt1 = "What is the capital of Japan?"
    print(f"Prompt: {prompt1}")
    print("Before editing:")
    before_edit1 = llm.generate_text(prompt1)
    print(before_edit1)
    
    print("\nEditing knowledge...")
    success1 = llm.edit_knowledge(
        subject="Japan",
        target_fact="Osaka is the capital of Japan",
        original_fact="Tokyo is the capital of Japan"
    )
    
    print(f"Edit successful: {success1}")
    
    print("\nAfter editing:")
    after_edit1 = llm.generate_text(prompt1)
    print(after_edit1)
    
    if "Osaka" in after_edit1 and "Tokyo" not in after_edit1:
        print("\n✅ Knowledge successfully edited!")
    else:
        print("\n❌ Knowledge editing failed or incomplete")
    
    print("\n\n--- Test 2: Editing Knowledge about Programming Languages ---")
    
    prompt2 = "When was Python created and by whom?"
    print(f"Prompt: {prompt2}")
    print("Before editing:")
    before_edit2 = llm.generate_text(prompt2)
    print(before_edit2)
    
    print("\nEditing knowledge...")
    success2 = llm.edit_knowledge(
        subject="Python programming language",
        target_fact="Python was created by Guido van Rossum in 1989",
        original_fact="Python was created by Guido van Rossum in 1991"
    )
    
    print(f"Edit successful: {success2}")
    
    print("\nAfter editing:")
    after_edit2 = llm.generate_text(prompt2)
    print(after_edit2)
    
    if "1989" in after_edit2:
        print("\n✅ Knowledge successfully edited!")
    else:
        print("\n❌ Knowledge editing failed or incomplete")
    
    print("\n\n--- Test 3: Multiple Edits and Persistence ---")
    
    print("Adding another edit...")
    success3 = llm.edit_knowledge(
        subject="Python programming language",
        target_fact="Python was initially designed as a hobby project",
        original_fact=None  # 元の事実を指定しない場合もある
    )
    
    print(f"Edit successful: {success3}")
    
    prompt3 = "Tell me about the history of Python programming language."
    print(f"\nPrompt: {prompt3}")
    after_multiple_edits = llm.generate_text(prompt3)
    print(after_multiple_edits)
    
    if "1989" in after_multiple_edits and "hobby project" in after_multiple_edits.lower():
        print("\n✅ Multiple edits successfully applied!")
    else:
        print("\n❌ Some edits were not applied correctly")
    
    print("\n\n--- Test 4: Edit Persistence Across Sessions ---")
    print("Creating a new LLM instance...")
    
    new_llm = LLM(
        api_key=api_key,
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    )
    new_llm.set_rome_model_editor(rome_editor)
    
    print(f"\nPrompt: {prompt2}")
    persistence_check = new_llm.generate_text(prompt2)
    print(persistence_check)
    
    if "1989" in persistence_check:
        print("\n✅ Edits persist across LLM instances!")
    else:
        print("\n❌ Edits do not persist across instances")
    
    print("\n=== ROME Knowledge Editing Demonstration Complete ===")

if __name__ == "__main__":
    demonstrate_rome_knowledge_editing()
