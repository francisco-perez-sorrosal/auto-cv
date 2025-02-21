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

# Run crews

```
pixi run run_cv_adaptor_crew
pixi run run_cv_compiler_crew
```

### Shiny app

Note: the ui pixi task includes `-r` option to autoreload the application.
```pixi run ui```

### Run just the Crew (TODO: FIX IF NECESSARY - NOT WORKING WELL BC UV INTERFERES WITH PIXI)

0. Setup the project as shown above
1. Rename `.env.example` to `.env`
```mv .env.example .env```
2. Edit `.env` with your own values
3. Install the crew:
```pixi run crewai install```
4. Run the crew:
```pixi run crewai run```
