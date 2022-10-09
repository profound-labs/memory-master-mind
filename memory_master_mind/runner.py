#!/usr/bin/env python3

import sys
import typer

app = typer.Typer()
index_app = typer.Typer()
app.add_typer(index_app, name="index")

@app.command()
def cli():
    from memory_master_mind.app import start
    start()

def main():
    if len(sys.argv) == 1:
        cli()
    else:
        app()

if __name__ == "__main__":
    main()
