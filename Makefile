# Build/Release package configuration
release:
	cd cis-webhook && kctrl package release -y -v ${VERSION}
	cp cis-webhook/carvel-artifacts/packages/cis-webhook.field.vmware.com/metadata.yml ./config/cis-webhook-package.yml
	echo "\n---" >> ./config/cis-webhook-package.yml
	cat cis-webhook/carvel-artifacts/packages/cis-webhook.field.vmware.com/package.yml >> ./config/cis-webhook-package.yml
	IMAGE=$(shell yq -r 'select(.kind == "Package") | .spec.template.spec.fetch[0].imgpkgBundle.image' config/cis-webhook-package.yml); \
	echo $${IMAGE}; \
	yq e -i ".cis_webhook_package = \"$$IMAGE\"" config/values.yaml;
	yq e -i ".cis_webhook_version = \"$$VERSION\"" config/values.yaml;
	kctrl package release -y -v ${VERSION}
	cp carvel-artifacts/packages/cis-service.fling.vsphere.vmware.com/metadata.yml ./cis-service.yml
	echo "\n---" >> ./cis-service.yml
	cat carvel-artifacts/packages/cis-service.fling.vsphere.vmware.com/package.yml >> ./cis-service.yml
