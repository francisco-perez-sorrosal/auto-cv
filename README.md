# Auto CV

Automated CV generation tool built with Python and Pixi.

## Setup

1. Install [Pixi](https://pixi.sh/)
2. Clone the repository
3. Run `pixi install` to set up the environment

## Development

- Run tests: `pixi run test`
- Lint code: `pixi run lint`
- Format code: `pixi run format`
- Type check: `pixi run typecheck`

Update llm-foundation dependency
pixi update

## Usage

Install the crew:

```pixi run crewai install```

Run the crew:

```pixi run crewai run```

## Streamlit app

To run the Streamlit app: 

```pixi run streamlit run src/auto_cv/ui/main_app.py```
