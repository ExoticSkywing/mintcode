COMPOSE=docker compose -f docker-compose.dev.yml

ADMIN_API_KEY?=change-me
VOUCHER_SECRET?=change-me-too
FIVESIM_API_KEY?=dummy

export ADMIN_API_KEY
export VOUCHER_SECRET
export FIVESIM_API_KEY

.PHONY: up-dev down-dev alembic-upgrade regress-dev-security regress-buy-guard ci ci-clean

up-dev:
	$(COMPOSE) up -d --build mysql api worker

down-dev:
	$(COMPOSE) down -v

alembic-upgrade:
	$(COMPOSE) exec -T api sh -lc 'alembic upgrade head'

regress-dev-security:
	python regress_dev_security.py

regress-buy-guard:
	python regress_buy_guard_lease.py

ci: regress-dev-security regress-buy-guard

ci-clean:
	REGRESS_CLEANUP=1 $(MAKE) ci
