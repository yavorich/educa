from typing import Any, Optional
from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model


class OrderField(models.PositiveIntegerField):
    def __init__(self, for_fields: Optional[Any]=None, *args: Any, **kwargs: Any) -> None:
        '''
        for_fields - поля, по которым будут упорядочиваться данные
        '''
        self.for_fields = for_fields
        super().__init__(*args, **kwargs)
    
    def pre_save(self, model_instance: Model, add: bool) -> Any:
        if getattr(model_instance, self.attname) is None:
            # текущее значение поля PositiveIntegerField отсутствует
            try:
                qs = self.model.objects.all()
                if self.for_fields:
                    # фильтровать по полям for_fields
                    query = {field: getattr(model_instance, field)
                             for field in self.for_fields}
                    qs = qs.filter(**query)
                last_item = qs.latest(self.attname)
                value = last_item.order + 1
            except ObjectDoesNotExist:
                value = 0
            setattr(model_instance, self.attname, value)
            return value
        else:            
            return super().pre_save(model_instance, add)
