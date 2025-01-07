"""Script to run performance tests and generate a report."""

import os
import sys
import asyncio
import json
import datetime
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

import pytest
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceReport:
    """Generate performance test report."""
    
    def __init__(self, results_dir: str = "performance_results"):
        """Initialize report generator."""
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def create_report(self, test_results: dict):
        """Create performance report from test results."""
        # Create results directory for this run
        run_dir = self.results_dir / f"run_{self.timestamp}"
        run_dir.mkdir(exist_ok=True)
        
        # Save raw results
        with open(run_dir / "raw_results.json", "w") as f:
            json.dump(test_results, f, indent=2)
        
        # Generate summary statistics
        summary = self._generate_summary(test_results)
        with open(run_dir / "summary.json", "w") as f:
            json.dump(summary, f, indent=2)
        
        # Create visualizations
        self._create_visualizations(test_results, run_dir)
        
        # Generate HTML report
        self._generate_html_report(summary, test_results, run_dir)
        
        logger.info(f"Performance report generated in {run_dir}")
        return run_dir
    
    def _generate_summary(self, results: dict) -> dict:
        """Generate summary statistics from test results."""
        summary = {
            "timestamp": self.timestamp,
            "overall": {
                "total_tests": len(results),
                "passed": sum(1 for r in results.values() if r["status"] == "passed"),
                "failed": sum(1 for r in results.values() if r["status"] == "failed")
            },
            "performance": {}
        }
        
        # Calculate performance metrics
        for test_name, test_data in results.items():
            if "stats" in test_data:
                stats = test_data["stats"]
                if "response_times" in stats:
                    rt = stats["response_times"]
                    summary["performance"][f"{test_name}_response_time"] = {
                        "mean": rt["mean"],
                        "p95": rt["p95"]
                    }
                
                if "memory_operations" in stats:
                    mo = stats["memory_operations"]
                    summary["performance"][f"{test_name}_memory_ops"] = {
                        "mean": mo["mean"],
                        "p95": mo["p95"]
                    }
        
        return summary
    
    def _create_visualizations(self, results: dict, output_dir: Path):
        """Create performance visualizations."""
        # Response time distribution
        plt.figure(figsize=(12, 6))
        data = []
        for test_name, test_data in results.items():
            if "stats" in test_data and "response_times" in test_data["stats"]:
                rt = test_data["stats"]["response_times"]
                data.append({
                    "test": test_name,
                    "mean": rt["mean"],
                    "p95": rt["p95"]
                })
        
        if data:
            df = pd.DataFrame(data)
            plt.figure(figsize=(12, 6))
            sns.barplot(data=df, x="test", y="mean", color="blue", alpha=0.5, label="Mean")
            sns.barplot(data=df, x="test", y="p95", color="red", alpha=0.5, label="95th Percentile")
            plt.xticks(rotation=45)
            plt.title("Response Time Distribution")
            plt.ylabel("Time (ms)")
            plt.legend()
            plt.tight_layout()
            plt.savefig(output_dir / "response_times.png")
            plt.close()
        
        # Memory operations
        plt.figure(figsize=(12, 6))
        data = []
        for test_name, test_data in results.items():
            if "stats" in test_data and "memory_operations" in test_data["stats"]:
                mo = test_data["stats"]["memory_operations"]
                data.append({
                    "test": test_name,
                    "mean": mo["mean"],
                    "p95": mo["p95"]
                })
        
        if data:
            df = pd.DataFrame(data)
            plt.figure(figsize=(12, 6))
            sns.barplot(data=df, x="test", y="mean", color="green", alpha=0.5, label="Mean")
            sns.barplot(data=df, x="test", y="p95", color="orange", alpha=0.5, label="95th Percentile")
            plt.xticks(rotation=45)
            plt.title("Memory Operation Times")
            plt.ylabel("Time (ms)")
            plt.legend()
            plt.tight_layout()
            plt.savefig(output_dir / "memory_operations.png")
            plt.close()
        
        # Error distribution
        plt.figure(figsize=(12, 6))
        data = []
        for test_name, test_data in results.items():
            if "stats" in test_data and "errors" in test_data["stats"]:
                errors = test_data["stats"]["errors"]
                data.append({
                    "test": test_name,
                    "errors": errors["count"]
                })
        
        if data:
            df = pd.DataFrame(data)
            plt.figure(figsize=(12, 6))
            sns.barplot(data=df, x="test", y="errors", color="red")
            plt.xticks(rotation=45)
            plt.title("Error Distribution")
            plt.ylabel("Error Count")
            plt.tight_layout()
            plt.savefig(output_dir / "errors.png")
            plt.close()
    
    def _generate_html_report(self, summary: dict, results: dict, output_dir: Path):
        """Generate HTML performance report."""
        html = f"""
        <html>
        <head>
            <title>Performance Test Report - {self.timestamp}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1, h2 {{ color: #333; }}
                .summary {{ margin: 20px 0; padding: 10px; background: #f5f5f5; }}
                .test-results {{ margin: 20px 0; }}
                .test {{ margin: 10px 0; padding: 10px; border: 1px solid #ddd; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
                .visualization {{ margin: 20px 0; }}
                img {{ max-width: 100%; height: auto; }}
            </style>
        </head>
        <body>
            <h1>Performance Test Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p>Timestamp: {summary["timestamp"]}</p>
                <p>Total Tests: {summary["overall"]["total_tests"]}</p>
                <p>Passed: <span class="passed">{summary["overall"]["passed"]}</span></p>
                <p>Failed: <span class="failed">{summary["overall"]["failed"]}</span></p>
            </div>
            
            <div class="visualizations">
                <h2>Visualizations</h2>
                <div class="visualization">
                    <h3>Response Times</h3>
                    <img src="response_times.png" alt="Response Time Distribution">
                </div>
                <div class="visualization">
                    <h3>Memory Operations</h3>
                    <img src="memory_operations.png" alt="Memory Operation Times">
                </div>
                <div class="visualization">
                    <h3>Errors</h3>
                    <img src="errors.png" alt="Error Distribution">
                </div>
            </div>
            
            <div class="test-results">
                <h2>Detailed Results</h2>
        """
        
        # Add test results
        for test_name, test_data in results.items():
            status_class = "passed" if test_data["status"] == "passed" else "failed"
            html += f"""
                <div class="test">
                    <h3>{test_name} - <span class="{status_class}">{test_data["status"]}</span></h3>
            """
            
            if "stats" in test_data:
                stats = test_data["stats"]
                if "response_times" in stats:
                    rt = stats["response_times"]
                    html += f"""
                    <h4>Response Times (ms)</h4>
                    <ul>
                        <li>Mean: {rt["mean"]:.2f}</li>
                        <li>Median: {rt["median"]:.2f}</li>
                        <li>95th Percentile: {rt["p95"]:.2f}</li>
                        <li>Min: {rt["min"]:.2f}</li>
                        <li>Max: {rt["max"]:.2f}</li>
                    </ul>
                    """
                
                if "memory_operations" in stats:
                    mo = stats["memory_operations"]
                    html += f"""
                    <h4>Memory Operations (ms)</h4>
                    <ul>
                        <li>Mean: {mo["mean"]:.2f}</li>
                        <li>Median: {mo["median"]:.2f}</li>
                        <li>95th Percentile: {mo["p95"]:.2f}</li>
                        <li>Min: {mo["min"]:.2f}</li>
                        <li>Max: {mo["max"]:.2f}</li>
                    </ul>
                    """
                
                if "concurrent_operations" in stats:
                    co = stats["concurrent_operations"]
                    html += f"""
                    <h4>Concurrent Operations</h4>
                    <ul>
                        <li>Mean: {co["mean"]:.2f}</li>
                        <li>Max: {co["max"]}</li>
                        <li>Total: {co["total"]}</li>
                    </ul>
                    """
                
                if "errors" in stats:
                    errors = stats["errors"]
                    html += f"""
                    <h4>Errors</h4>
                    <ul>
                        <li>Count: {errors["count"]}</li>
                    """
                    if errors["messages"]:
                        html += "<li>Messages:<ul>"
                        for msg in errors["messages"]:
                            html += f"<li>{msg}</li>"
                        html += "</ul></li>"
                    html += "</ul>"
            
            html += "</div>"
        
        html += """
            </div>
        </body>
        </html>
        """
        
        with open(output_dir / "report.html", "w") as f:
            f.write(html)

def run_performance_tests():
    """Run performance tests and generate report."""
    logger.info("Starting performance tests")
    
    # Run pytest with performance marker
    test_results = {}
    
    # Run all tests at once
    result = pytest.main([
        "-v",
        "-m", "performance",
        "tests/nova/test_performance.py",
        "--capture=no",
        "-p", "no:warnings",  # Disable warning capture
        "--asyncio-mode=auto"  # Enable auto mode for asyncio
    ])
    
    # Map test results
    test_results = {
        "memory": {"status": "passed" if result == 0 else "failed", "stats": {}},
        "swarm": {"status": "passed" if result == 0 else "failed", "stats": {}},
        "profile": {"status": "passed" if result == 0 else "failed", "stats": {}},
        "graph": {"status": "passed" if result == 0 else "failed", "stats": {}},
        "agent": {"status": "passed" if result == 0 else "failed", "stats": {}}
    }
    
    # Generate report
    logger.info("Generating performance report")
    report = PerformanceReport()
    report_dir = report.create_report(test_results)
    
    logger.info(f"Performance testing complete. Report available at: {report_dir}")

if __name__ == "__main__":
    run_performance_tests()
