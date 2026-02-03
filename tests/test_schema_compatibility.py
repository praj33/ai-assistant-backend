"""
Automated Schema Compatibility Tests
Ensures zero schema drift and frontend safety.
"""

import pytest
from app.core.schema_validator import schema_validator


class TestSchemaCompatibility:
    """Test suite for locked contract compliance."""

    def test_request_schema_validation(self):
        """Test that valid requests pass validation."""
        valid_request = {
            "version": "3.0.0",
            "input": {
                "message": "Hello assistant"
            },
            "context": {
                "platform": "web",
                "device": "desktop"
            }
        }

        # Should not raise exception
        validated = schema_validator.validate_request(valid_request)
        assert validated.version == "3.0.0"
        assert validated.input.message == "Hello assistant"

    def test_request_schema_with_summary(self):
        """Test request with summarized payload."""
        valid_request = {
            "version": "3.0.0",
            "input": {
                "summarized_payload": {
                    "summary": "Test summary"
                }
            },
            "context": {
                "platform": "mobile",
                "device": "phone",
                "voice_input": True
            }
        }

        validated = schema_validator.validate_request(valid_request)
        assert validated.input.summarized_payload["summary"] == "Test summary"

    def test_invalid_request_schema(self):
        """Test that invalid requests fail validation."""
        invalid_request = {
            "version": "2.0.0",  # Wrong version
            "input": {
                "message": "Hello"
            },
            "context": {
                "platform": "web",
                "device": "desktop"
            }
        }

        with pytest.raises(ValueError):
            schema_validator.validate_request(invalid_request)

    def test_response_schema_validation(self):
        """Test that valid responses pass validation."""
        valid_response = {
            "version": "3.0.0",
            "status": "success",
            "result": {
                "type": "passive",
                "response": "Hello user!"
            },
            "processed_at": "2023-01-01T00:00:00Z"
        }

        # Should not raise exception
        assert schema_validator.validate_response(valid_response)

    def test_error_response_schema_validation(self):
        """Test error response validation."""
        error_response = {
            "version": "3.0.0",
            "status": "error",
            "error": {
                "code": "INVALID_INPUT",
                "message": "Bad input"
            },
            "processed_at": "2023-01-01T00:00:00Z"
        }

        assert schema_validator.validate_response(error_response)

    def test_workflow_response_with_task(self):
        """Test workflow response with task data."""
        workflow_response = {
            "version": "3.0.0",
            "status": "success",
            "result": {
                "type": "workflow",
                "response": "Task created successfully",
                "task": {
                    "type": "reminder",
                    "parameters": {"message": "Test"},
                    "priority": "high"
                }
            },
            "processed_at": "2023-01-01T00:00:00Z"
        }

        assert schema_validator.validate_response(workflow_response)
