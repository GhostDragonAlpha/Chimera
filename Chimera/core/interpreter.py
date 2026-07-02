import json
import os

class WorkflowInterpreter:
    def __init__(self, registry_path, output_dir):
        with open(registry_path, 'r') as f:
            self.registry = json.load(f)['terms']
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def execute_and_save(self, dsl_data, workflow_id):
        workflow_output = {
            "workflow_id": workflow_id,
            "steps": []
        }
        for step in dsl_data.get('steps', []):
            operation = step.get('operation')
            source_uid = step.get('source_uid')
            target_uid = step.get('target_uid')
            
            step_output = {
                "step_id": step.get('step_id'),
                "operation": operation,
                "source_uid": source_uid
            }
            if target_uid:
                step_output["target_uid"] = target_uid
            if 'condition' in step and step['condition']:
                step_output["condition"] = step['condition']
            if 'confidence_score' in step and step['confidence_score'] is not None:
                step_output["confidence_score"] = step['confidence_score']
                
            workflow_output["steps"].append(step_output)
        
        output_file = os.path.join(self.output_dir, f"{workflow_id}.json")
        with open(output_file, 'w') as f:
            json.dump(workflow_output, f, indent=2)
        return output_file
