#!/usr/bin/env python3

import requests
import json
import time

def test_langgraph_workflow():
    print("Testing LangGraph workflow...")

    try:
        # 创建会话
        print("1. Creating session...")
        response = requests.post('http://localhost:8000/api/session')
        session_data = response.json()
        session_id = session_data['session_id']
        print(f"   Created session: {session_id}")

        # 运行工作流
        print("2. Running workflow...")
        workflow_data = {
            'session_id': session_id,
            'user_text': '给我一个机械专业「液压传动原理」的理论课课件，10页左右',
            'answers': {},
            'auto_fill_defaults': True
        }
        response = requests.post('http://localhost:8000/api/workflow/run', json=workflow_data)
        result = response.json()
        print(f"   Status: {result['status']}")
        print(f"   Stage: {result['stage']}")

        if 'teaching_request' in result and result['teaching_request']:
            tr = result['teaching_request']
            subject_info = tr.get('subject_info', {})
            print(f"   Subject: {subject_info.get('subject_name', 'N/A')}")
            print(f"   Category: {subject_info.get('subject_category', 'N/A')}")
            print(f"   Knowledge points: {len(tr.get('knowledge_points', []))}")

        if 'outline' in result and result['outline']:
            outline = result['outline']
            slides = outline.get('slides', [])
            print(f"   Outline slides: {len(slides)}")

        print("3. Checking logs...")
        logs_response = requests.get(f'http://localhost:8000/api/logs/{session_id}')
        if logs_response.status_code == 200:
            logs = logs_response.text.split('\n')
            print(f"   Total log entries: {len([l for l in logs if l.strip()])}")

            # 显示最后几条日志
            recent_logs = [l for l in logs[-10:] if l.strip()]
            for log in recent_logs:
                try:
                    log_data = json.loads(log)
                    stage = log_data.get('stage', 'N/A')
                    kind = log_data.get('kind', 'N/A')
                    print(f"     [{stage}] {kind}")
                except:
                    pass

        print("✅ Test completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # 等待服务器启动
    print("Waiting for server to start...")
    time.sleep(2)
    test_langgraph_workflow()