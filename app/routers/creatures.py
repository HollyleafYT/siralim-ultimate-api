from typing import Dict, List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import contains_eager, selectinload
from sqlalchemy.orm.attributes import InstrumentedAttribute

from app.orm.creature import CreatureOrm
from app.models.creature import CreatureModel
from app.orm.klass import KlassOrm
from app.orm.race import RaceOrm
from app.orm.trait import TraitOrm
from .helpers import (
    PaginationSchema,
    build_sorting_schema,
    select,
    has_session,
    has_pagination,
    has_sorting,
)

router = APIRouter(
    prefix="/creatures",
    tags=["creatures"],
)

SortingSchema = build_sorting_schema(
    [
        CreatureOrm.id,
        CreatureOrm.name,
        CreatureOrm.health,
        CreatureOrm.attack,
        CreatureOrm.intelligence,
        CreatureOrm.defense,
        CreatureOrm.speed,
        CreatureOrm.klass_id,
        CreatureOrm.klass_name,
        CreatureOrm.race_id,
        CreatureOrm.race_name,
        CreatureOrm.trait_id,
        CreatureOrm.trait_name,
    ]
)

EAGER_LOAD_OPTIONS = (
    contains_eager(CreatureOrm.klass),
    contains_eager(CreatureOrm.race),
    contains_eager(CreatureOrm.trait),
    selectinload(CreatureOrm.race, RaceOrm.default_klass),
    selectinload(CreatureOrm.sources),
)


class IndexSchema(BaseModel):
    data: List[CreatureModel]
    pagination: PaginationSchema
    sorting: SortingSchema


pagination_depend = has_pagination()
sorting_depend = has_sorting(SortingSchema, "id")


@router.get("/", response_model=IndexSchema)
def index(
    session=Depends(has_session),
    pagination: PaginationSchema = Depends(pagination_depend),
    sorting: SortingSchema = Depends(sorting_depend),
):
    creatures_orm = (
        select(CreatureOrm)
        .join(RaceOrm)
        .join(KlassOrm, CreatureOrm.klass_id == KlassOrm.id)
        .join(TraitOrm)
        .options(*EAGER_LOAD_OPTIONS)
        .pagination(pagination)
        .sorting(sorting)
        .get_scalars(session)
    )
    creatures_model = CreatureModel.from_orm_list(creatures_orm)
    return IndexSchema(
        data=creatures_model, pagination=pagination, sorting=SortingSchema
    )


class GetSchema(BaseModel):
    data: CreatureModel


@router.get("/{creature_id}", response_model=GetSchema)
def get(creature_id: str, session=Depends(has_session)):
    creatures_orm = (
        select(CreatureOrm)
        .join(RaceOrm)
        .join(KlassOrm, CreatureOrm.klass_id == KlassOrm.id)
        .join(TraitOrm)
        .options(*EAGER_LOAD_OPTIONS)
        .where(CreatureOrm.where_slug_or_id(creature_id))
        .get_scalar(session)
    )
    creatures_model = CreatureModel.from_orm(creatures_orm)
    return GetSchema(data=creatures_model)
