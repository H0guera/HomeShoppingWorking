from django.db.models import Manager
from rest_framework import serializers


class UpdateListSerializer(serializers.ListSerializer):

    def select_existing_item(self, manager, datum):
        pass

    def get_field_name_and_rel_instance(self, manager):
        return manager.field.name, manager.instance

    def update(self, instance, validated_data):
        assert isinstance(instance, Manager)

        items = []
        field_name, rel_instance = self.get_field_name_and_rel_instance(instance)
        for validated_datum in validated_data:
            complete_validated_datum = {field_name: rel_instance}
            complete_validated_datum.update(validated_datum)
            existing_item = self.select_existing_item(instance, complete_validated_datum)

            if existing_item is not None:
                updated_instance = self.child.update(existing_item, complete_validated_datum)
            else:
                updated_instance = self.child.create(complete_validated_datum)
            items.append(updated_instance)

        return items


class UpdateRelationMixin:
    def update_relation(self, name, manager, values):
        if values is None:
            return
        serializer = self.fields[name]

        updated_values = serializer.update(manager, values)

        if self.partial:
            manager.add(*updated_values)
        elif hasattr(manager, 'field') and not manager.field.null:
            # add the updated_attribute_values to the instance
            manager.add(*updated_values)
            # remove all the obsolete attribute values, this could be caused by
            # the product class changing for example, lots of attributes would become
            # obsolete.
            current_pks = [p.pk for p in updated_values]
            manager.exclude(pk__in=current_pks).delete()
        else:
            manager.set(updated_values)
