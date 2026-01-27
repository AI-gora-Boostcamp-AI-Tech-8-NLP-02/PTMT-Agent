# uv run python core/tests/curriculum_compose_agent_test.py
import os
import sys
import asyncio
import json
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
from core.agents.curriculum_compose_agent import CurriculumComposeAgent
from core.contracts.curriculum_compose import CurriculumComposeInput
from core.llm.solar_pro_2_llm import get_solar_model


async def main():
    load_dotenv()
    llm = get_solar_model("solar-pro3",temperature=0.1)
    
    # 데이터 로드
    data_dir = project_root / "tests" / "dummy_data"
    user_path = data_dir / "dummy_user_information.json"
    curriculum_path = data_dir / "dummy_initial_curriculum.json"
    
    with open(user_path, "r") as f:
        user_info = json.load(f)
    with open(curriculum_path, "r") as f:
        curriculum_data = json.load(f)

    # Agent 생성
    agent = CurriculumComposeAgent(llm=llm)
    
    # 입력 구성
    input_data: CurriculumComposeInput = {
        "user_info": user_info,
        "curriculum": curriculum_data
    }

    print("🚀 테스트 시작: Curriculum Compose Agent (Global Optimization)")
    
    # 초기 리소스 수 및 로드 계산
    nodes_before = curriculum_data["nodes"]
    total_res_before = sum(len(n.get("resources", [])) for n in nodes_before)
    
    # 로드 계산 (문자열 '3.0' 등을 float으로)
    total_load_before = 0.0
    for n in nodes_before:
        for r in n.get("resources", []):
            try:
                load = float(r.get("study_load", 0))
            except:
                load = 0.0
            total_load_before += load

    user_budget = float(user_info.get("budgeted_time", {}).get("total_hours", 25))
    
    print(f"User Budget: {user_budget}h")
    print(f"Original Total Resources: {total_res_before}")
    print(f"Original Total Load: {total_load_before:.1f}h")
    print("=" * 60)
    
    result = await agent.run(input_data)
    
    new_curriculum = result["curriculum"]
    new_nodes = new_curriculum["nodes"]
    
    # 결과 로드 계산
    total_res_after = 0
    emphasize_load = 0.0
    preserve_load = 0.0
    
    print("\n[상세 변경 내역 (Resources)]")
    for n in new_nodes:
        print(f"\n[{n['keyword']}]")
        for r in n.get("resources", []):
            total_res_after += 1
            load = float(r.get("study_load", 0) or 0)
            
            # 상태 출력 및 로드 집계
            if r.get("is_necessary"):
                status = "🔴 EMPHASIZE"
                emphasize_load += load
            else:
                status = "⚪ PRESERVE"
                preserve_load += load
                
            print(f"  {status} : {r['resource_name']} ({load}h)")

    print("\n" + "=" * 60)
    print("✅ 테스트 완료 및 결과 분석")
    print("=" * 60)
    
    total_load_after = emphasize_load + preserve_load
    
    print(f"Final Total Resources: {total_res_after} (Original: {total_res_before})")
    print(f"Deleted Resources: {total_res_before - total_res_after}")
    print("-" * 40)
    print(f"Goal Budget: {user_budget}h")
    print(f"🔴 EMPHASIZE Load: {emphasize_load:.1f}h")
    print(f"⚪ PRESERVE Load: {preserve_load:.1f}h")
    print(f"Total Load (EMP + PRE): {total_load_after:.1f}h")
    
    if emphasize_load <= user_budget + 2.0: # 2시간 정도의 오차 허용
        print("🎉 성공: EMPHASIZE Load가 예산 범위(오차 포함) 내로 최적화됨")
    else:
        print(f"⚠️ 주의: EMPHASIZE Load({emphasize_load:.1f}h)가 예산({user_budget}h)을 다소 초과함.")

if __name__ == "__main__":
    asyncio.run(main())
