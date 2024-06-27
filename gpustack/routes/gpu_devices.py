from fastapi import APIRouter
from gpustack.server.deps import ListParamsDep, SessionDep
from gpustack.schemas.gpu_devices import (
    GPUDevice,
    GPUDevicesPublic,
    GPUDevicePublic,
)
from gpustack.api.exceptions import (
    NotFoundException,
)


router = APIRouter()


@router.get("", response_model=GPUDevicesPublic)
async def get_gpus(session: SessionDep, params: ListParamsDep):
    fields = {}
    if params.query:
        fields = {"name": params.query}

    return await GPUDevice.paginated_by_query(
        session=session,
        fields=fields,
        page=params.page,
        per_page=params.perPage,
    )


@router.get("/{id}", response_model=GPUDevicePublic)
async def get_gpu(session: SessionDep, id: str):
    model = await GPUDevice.one_by_id(session, id)
    if not model:
        raise NotFoundException(message="GPU device not found")

    return model
