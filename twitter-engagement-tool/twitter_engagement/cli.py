"""Command Line Interface for Twitter Engagement Tool"""

import asyncio
import click
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint
from typing import Optional

from .database import AccountDatabase
from .parser import AccountParser
from .converter import RettwiConverter
from .utils import format_datetime, truncate_string, validate_twitter_cookies


console = Console()


@click.group()
@click.pass_context
def cli(ctx):
    """Twitter Engagement Tool - Manage multiple Twitter accounts with Rettiwt API"""
    ctx.ensure_object(dict)
    ctx.obj['db'] = AccountDatabase()


@cli.command()
@click.pass_context
def init_db(ctx):
    """Initialize the database"""
    async def _init():
        db = ctx.obj['db']
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Initializing database...", total=None)
            await db.init_db()
            progress.update(task, completed=True)
        
        console.print("[green]✓[/green] Database initialized successfully!")
    
    asyncio.run(_init())


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--format', 'line_format', 
              default='username:password:email:email_password:cookies',
              help='Format of each line in the file')
@click.pass_context
def add_accounts(ctx, file_path: str, line_format: str):
    """Add accounts from a file"""
    async def _add():
        db = ctx.obj['db']
        await db.init_db()
        
        try:
            # Parse accounts
            console.print(f"[cyan]Parsing accounts from {file_path}...[/cyan]")
            accounts = AccountParser.parse_file(file_path, line_format)
            console.print(f"[green]✓[/green] Found {len(accounts)} accounts")
            
            # Add to database
            added = 0
            updated = 0
            failed = 0
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Adding accounts...", total=len(accounts))
                
                for account in accounts:
                    try:
                        # Check if account exists
                        existing = await db.get_account(account.username)
                        
                        # Validate cookies if present
                        if account.cookies:
                            if not validate_twitter_cookies(account.cookies):
                                console.print(f"[yellow]⚠[/yellow] {account.username}: Invalid cookies (missing required fields)")
                        
                        await db.add_account(account)
                        
                        if existing:
                            updated += 1
                        else:
                            added += 1
                    except Exception as e:
                        console.print(f"[red]✗[/red] Failed to add {account.username}: {str(e)}")
                        failed += 1
                    
                    progress.advance(task)
            
            # Summary
            console.print("\n[bold]Summary:[/bold]")
            console.print(f"  [green]Added:[/green] {added}")
            console.print(f"  [blue]Updated:[/blue] {updated}")
            console.print(f"  [red]Failed:[/red] {failed}")
            
        except Exception as e:
            console.print(f"[red]Error:[/red] {str(e)}")
            raise click.Abort()
    
    asyncio.run(_add())


@cli.command()
@click.pass_context
def convert_rettiwt(ctx):
    """Convert accounts to Rettiwt API format"""
    async def _convert():
        db = ctx.obj['db']
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating Rettiwt API keys...", total=None)
            
            results = await db.generate_rettiwt_keys()
            progress.update(task, completed=True)
        
        # Display results
        if results:
            table = Table(title="Rettiwt API Key Generation Results")
            table.add_column("Username", style="cyan")
            table.add_column("API Key", style="green")
            table.add_column("Status", style="yellow")
            
            success_count = 0
            for username, result in results.items():
                if result.startswith("Error:"):
                    table.add_row(username, "-", f"[red]{result}[/red]")
                else:
                    table.add_row(username, truncate_string(result, 40), "[green]Success[/green]")
                    success_count += 1
            
            console.print(table)
            console.print(f"\n[green]✓[/green] Generated {success_count}/{len(results)} API keys successfully")
        else:
            console.print("[yellow]No accounts with cookies found to convert[/yellow]")
    
    asyncio.run(_convert())


@cli.command()
@click.option('--active-only', is_flag=True, help='Show only active accounts')
@click.option('--with-rettiwt', is_flag=True, help='Show only accounts with Rettiwt keys')
@click.pass_context
def list_accounts(ctx, active_only: bool, with_rettiwt: bool):
    """List all accounts"""
    async def _list():
        db = ctx.obj['db']
        
        if active_only:
            accounts = await db.get_active_accounts()
        else:
            accounts = await db.get_all_accounts()
        
        if with_rettiwt:
            accounts = [a for a in accounts if a.rettiwt_api_key]
        
        if not accounts:
            console.print("[yellow]No accounts found[/yellow]")
            return
        
        # Create table
        table = Table(title=f"Twitter Accounts ({len(accounts)} total)")
        table.add_column("Username", style="cyan")
        table.add_column("Email", style="white")
        table.add_column("Cookies", style="yellow")
        table.add_column("Rettiwt", style="green")
        table.add_column("Active", style="green")
        table.add_column("Created", style="white")
        table.add_column("Last Used", style="white")
        table.add_column("Error", style="red")
        
        for account in accounts:
            has_cookies = "✓" if account.cookies else "✗"
            has_rettiwt = "✓" if account.rettiwt_api_key else "✗"
            is_active = "[green]✓[/green]" if account.is_active else "[red]✗[/red]"
            
            table.add_row(
                account.username,
                account.email,
                has_cookies,
                has_rettiwt,
                is_active,
                format_datetime(account.created_at),
                format_datetime(account.last_used) if account.last_used else "-",
                truncate_string(account.error_msg, 30) if account.error_msg else "-"
            )
        
        console.print(table)
        
        # Show stats
        stats = await db.get_stats()
        console.print(f"\n[bold]Statistics:[/bold]")
        console.print(f"  Total accounts: {stats['total_accounts']}")
        console.print(f"  Active accounts: {stats['active_accounts']}")
        console.print(f"  With cookies: {stats['accounts_with_cookies']}")
        console.print(f"  With Rettiwt keys: {stats['accounts_with_rettiwt']}")
        console.print(f"  Failed: {stats['failed_accounts']}")
    
    asyncio.run(_list())


@cli.command()
@click.pass_context
def export_rettiwt(ctx):
    """Export Rettiwt credentials to JSON"""
    async def _export():
        db = ctx.obj['db']
        credentials = await db.get_rettiwt_credentials()
        
        if not credentials:
            console.print("[yellow]No Rettiwt credentials found[/yellow]")
            return
        
        # Create export data
        export_data = []
        for cred in credentials:
            export_data.append({
                'username': cred['username'],
                'apiKey': cred['api_key'],
                'cookies': cred['cookies'],
                'isActive': bool(cred['is_active']),
                'generatedAt': cred['generated_at']
            })
        
        # Write to file
        import json
        output_file = 'rettiwt_credentials.json'
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        console.print(f"[green]✓[/green] Exported {len(export_data)} credentials to {output_file}")
    
    asyncio.run(_export())


@cli.command()
@click.argument('username')
@click.pass_context
def delete_account(ctx, username: str):
    """Delete an account"""
    async def _delete():
        db = ctx.obj['db']
        
        account = await db.get_account(username)
        if not account:
            console.print(f"[red]Account '{username}' not found[/red]")
            return
        
        if click.confirm(f"Are you sure you want to delete account '{username}'?"):
            await db.delete_account(username)
            console.print(f"[green]✓[/green] Account '{username}' deleted successfully")
        else:
            console.print("[yellow]Deletion cancelled[/yellow]")
    
    asyncio.run(_delete())


@cli.command()
@click.argument('username')
@click.option('--activate/--deactivate', default=True, help='Activate or deactivate account')
@click.option('--error', help='Error message (when deactivating)')
@click.pass_context
def update_status(ctx, username: str, activate: bool, error: Optional[str]):
    """Update account status"""
    async def _update():
        db = ctx.obj['db']
        
        account = await db.get_account(username)
        if not account:
            console.print(f"[red]Account '{username}' not found[/red]")
            return
        
        await db.update_account_status(username, activate, error)
        status = "activated" if activate else "deactivated"
        console.print(f"[green]✓[/green] Account '{username}' {status}")
    
    asyncio.run(_update())


if __name__ == '__main__':
    cli()