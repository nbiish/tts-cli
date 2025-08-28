#!/usr/bin/env python3
"""
Main CLI Entry Point - TTS CLI Tool

Main command-line interface entry point for the TTS CLI tool.
Handles argument parsing and routes to appropriate functionality.

Author: Nbiish Waabanimii-Kinawaabakizi
Date: 2025
Version: 2.1
"""

import os
import sys
import argparse
from pathlib import Path
from rich.console import Console

# Add the project root to the Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tts_cli.core.environment_manager import MultiEnvironmentManager
from tts_cli.core.model_registry import ModelRegistry
from tts_cli.testing.model_tester import ModelTester

# Initialize console for rich output
console = Console()

def main():
    """Main function with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="CLI TTS Generator - Professional Text-to-Speech File Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Interactive CLI mode
  %(prog)s --text "Hello world"              # Generate speech from text
  %(prog)s --text "Hello world" --model f5-tts  # Use specific model
  %(prog)s --text "Hello world" --voice-clone voice.wav  # With voice cloning
  %(prog)s --clipboard                       # Read from clipboard
  %(prog)s --list-models                     # List available models
  %(prog)s --list-environments               # Show environment status
  %(prog)s --create-environment f5-tts      # Create isolated environment
  %(prog)s --cleanup-environment f5-tts     # Remove specific environment
  %(prog)s --cleanup-all-environments       # Remove all environments
  %(prog)s --text "Hello" --output speech.wav  # Specify output file
  %(prog)s --test-all-models                # Test all models
  %(prog)s --test-model f5-tts              # Test specific model
        """
    )
    
    parser.add_argument("--text", help="Text to convert to speech")
    parser.add_argument("--model", choices=["f5-tts", "edge-tts", "dia", "kyutai", "kokoro", "vibevoice"], 
                      default="f5-tts", help="TTS model to use")
    parser.add_argument("--voice-clone", help="Audio file for voice cloning")
    parser.add_argument("--clipboard", action="store_true", help="Read text from clipboard")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    parser.add_argument("--list-environments", action="store_true", help="List environment status for all models")
    parser.add_argument("--create-environment", help="Create isolated environment for specific model")
    parser.add_argument("--cleanup-environment", help="Remove isolated environment for specific model")
    parser.add_argument("--cleanup-all-environments", action="store_true",
                       help="Remove all isolated environments")
    parser.add_argument("--output", help="Output audio file path")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--test-model", help="Test specific model compatibility")
    parser.add_argument("--test-all-models", action="store_true", help="Test all models for compatibility")
    parser.add_argument("--benchmark-model", help="Benchmark specific model performance")
    parser.add_argument("--platform-info", action="store_true", help="Show detailed platform information")
    
    args = parser.parse_args()
    
    try:
        # Initialize core components
        env_manager = MultiEnvironmentManager()
        model_registry = ModelRegistry()
        
        # Handle different modes
        if args.list_models:
            show_models(model_registry)
            return
        
        if args.list_environments:
            show_environments(env_manager)
            return
        
        if args.create_environment:
            if args.create_environment not in model_registry.list_models():
                console.print(f"[red]❌ Unknown model: {args.create_environment}[/red]")
                return
            success = env_manager.create_environment(args.create_environment)
            if success:
                console.print(f"[green]✅ Environment created successfully for {args.create_environment}[/green]")
            else:
                console.print(f"[red]❌ Failed to create environment for {args.create_environment}[/red]")
            return
        
        if args.cleanup_environment:
            if args.cleanup_environment not in model_registry.list_models():
                console.print(f"[red]❌ Unknown model: {args.cleanup_environment}[/red]")
                return
            success = env_manager.cleanup_environment(args.cleanup_environment)
            if success:
                console.print(f"[green]✅ Environment removed successfully for {args.cleanup_environment}[/green]")
            else:
                console.print(f"[red]❌ Failed to remove environment for {args.cleanup_environment}[/red]")
            return
        
        if args.cleanup_all_environments:
            success = env_manager.cleanup_all_environments()
            if success:
                console.print("[green]✅ All environments removed successfully[/green]")
            else:
                console.print("[red]❌ Failed to remove all environments[/red]")
            return
        
        if args.test_all_models:
            test_all_models()
            return
        
        if args.test_model:
            if args.test_model not in model_registry.list_models():
                console.print(f"[red]❌ Unknown model: {args.test_model}[/red]")
                return
            test_single_model(args.test_model)
            return
        
        if args.platform_info:
            show_platform_info(model_registry)
            return
        
        if args.text or args.clipboard:
            # Non-interactive mode - placeholder for now
            console.print("[yellow]⚠️ Non-interactive mode not yet implemented in new architecture[/yellow]")
            console.print("[cyan]💡 Use --interactive for now, or wait for full implementation[/cyan]")
            return
        else:
            # Interactive mode (default)
            console.print("[yellow]⚠️ Interactive mode not yet implemented in new architecture[/yellow]")
            console.print("[cyan]💡 Use --list-models, --list-environments, or --test-all-models for now[/cyan]")
            return
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutdown requested. Goodbye![/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")

def show_models(model_registry: ModelRegistry):
    """Display available models in a formatted table."""
    from rich.table import Table
    
    table = Table(title="🎵 Available TTS Models")
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold")
    table.add_column("Voice Cloning", style="green")
    table.add_column("Platforms", style="blue")
    table.add_column("Description", style="white")
    
    for model_key in model_registry.list_models():
        model_info = model_registry.get_model_info(model_key)
        if model_info:
            voice_cloning = "✅ Yes" if model_info.get("voice_cloning", False) else "❌ No"
            platforms = ", ".join(model_info.get("platforms", []))
            
            table.add_row(
                model_info["name"],
                model_info["status"],
                voice_cloning,
                platforms,
                model_info["description"]
            )
    
    console.print(table)
    
    # Show summary
    summary = model_registry.get_model_status_summary()
    console.print(f"\n[bold]📊 Model Summary:[/bold]")
    console.print(f"Total Models: {summary['total_models']}")
    console.print(f"Implemented: {summary['implemented_models']}")
    console.print(f"Voice Cloning: {summary['voice_cloning_models']}")
    console.print(f"Current Device: {summary['current_device']}")
    console.print(f"Implementation Rate: {summary['implementation_rate']}")

def show_environments(env_manager: MultiEnvironmentManager):
    """Display environment status for all models."""
    from rich.table import Table
    
    table = Table(title="🔧 Environment Status")
    table.add_column("Model", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold")
    table.add_column("Path", style="blue")
    table.add_column("Packages", style="green")
    table.add_column("Description", style="white")
    
    env_statuses = env_manager.list_environments()
    
    for model_key, status in env_statuses.items():
        table.add_row(
            model_key,
            status["status"],
            status["path"],
            ", ".join(status["packages"]),
            status["description"]
        )
    
    console.print(table)

def test_all_models():
    """Test all models for compatibility and functionality."""
    console.print("[cyan]🧪 Testing all models...[/cyan]")
    
    tester = ModelTester()
    results = tester.test_all_models()
    
    # Display results
    console.print(tester.generate_test_report())
    
    # Save results
    tester.save_test_results()
    
    # Show health summary
    health = tester.get_model_health_summary()
    console.print(f"\n[bold]🏥 Model Health Summary:[/bold]")
    console.print(f"Total Models: {health['total_models']}")
    console.print(f"Passing: {health['passing_models']}")
    console.print(f"Partial: {health['partial_models']}")
    console.print(f"Failing: {health['failing_models']}")
    console.print(f"Success Rate: {health['success_rate']}")
    console.print(f"Health Score: {health['health_score']}")

def test_single_model(model_key: str):
    """Test a single model for compatibility and functionality."""
    console.print(f"[cyan]🧪 Testing model: {model_key}[/cyan]")
    
    tester = ModelTester()
    result = tester.test_single_model(model_key)
    
    # Display result
    console.print(f"\n[bold]Test Results for {model_key}:[/bold]")
    console.print(f"Status: {result['status']}")
    console.print(f"Overall Score: {result['overall_score']:.1f}")
    
    for test_name, test_result in result.get("tests", {}).items():
        console.print(f"\n{test_name.replace('_', ' ').title()}: {test_result['status']}")
        if "details" in test_result:
            console.print(f"  {test_result['details']}")

def show_platform_info(model_registry: ModelRegistry):
    """Show detailed platform information."""
    console.print("[bold]🖥️ Platform Information[/bold]")
    
    # Device detection
    device = model_registry.device
    console.print(f"Current Device: {device.upper()}")
    
    # Platform compatibility
    console.print(f"\n[bold]Platform Compatibility:[/bold]")
    for platform in ["CUDA", "MPS", "CPU"]:
        compatible_models = model_registry.get_models_by_platform(platform)
        console.print(f"{platform}: {len(compatible_models)} models")
    
    # Voice cloning support
    voice_cloning_models = model_registry.get_voice_cloning_models()
    console.print(f"\nVoice Cloning Support: {len(voice_cloning_models)} models")
    
    # Device-specific recommendations
    if device == "cpu":
        console.print("\n[yellow]⚠️ CPU Mode:[/yellow] Generation will be slower. Consider using lightweight models like Kokoro.")
    elif device == "mps":
        console.print("\n[cyan]🍎 Apple Silicon (MPS):[/cyan] Good performance with MPS-compatible models.")
    elif device == "cuda":
        console.print("\n[green]🚀 CUDA GPU:[/green] Optimal performance with all models.")

if __name__ == "__main__":
    main()
