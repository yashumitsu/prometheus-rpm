MANUAL = prometheus2 \
jmx_exporter \
rabbitmq_exporter \
ping_exporter \
mtail \

AUTO_GENERATED = alertmanager \
node_exporter \
blackbox_exporter \
snmp_exporter \
pushgateway \
mysqld_exporter \
elasticsearch_exporter \
postgres_exporter \
pgbouncer_exporter \
redis_exporter \
haproxy_exporter \
kafka_exporter \
nginx_exporter \
bind_exporter \
json_exporter \
mongodb_exporter \
statsd_exporter \
memcached_exporter \
consul_exporter \
smokeping_prober \
iperf3_exporter \
apache_exporter \
exporter_exporter \
process_exporter \
ssl_exporter \
ebpf_exporter \
karma \
artifactory_exporter \
phpfpm_exporter \
ipmi_exporter \
sql_exporter \
nats_exporter \
cadvisor \
dellhw_exporter \
systemd_exporter \
bird_exporter

.PHONY: $(MANUAL) $(AUTO_GENERATED)

INTERACTIVE:=$(shell [ -t 0 ] && echo 1)
ifdef INTERACTIVE
	DOCKER_FLAGS = -it --rm
else
	DOCKER_FLAGS = --rm
endif

all: auto manual

manual: $(MANUAL)
auto: $(AUTO_GENERATED)

manual9: $(addprefix build9-,$(MANUAL))

$(addprefix build9-,$(MANUAL)):
	$(eval PACKAGE=$(subst build9-,,$@))
	[ -d ${PWD}/_dist9 ] || mkdir ${PWD}/_dist9 
	[ -d ${PWD}/_cache_dnf ] || mkdir ${PWD}/_cache_dnf 
	docker run ${DOCKER_FLAGS} \
		-v ${PWD}/${PACKAGE}:/rpmbuild/SOURCES \
		-v ${PWD}/_dist9:/rpmbuild/RPMS/x86_64 \
		-v ${PWD}/_dist9:/rpmbuild/RPMS/noarch \
		-v ${PWD}/_cache_dnf:/var/cache/dnf \
		ghcr.io/yashumitsu/prometheus-rpm-builder-almalinux9 \
		build-spec SOURCES/${PACKAGE}.spec
	# Test the install
	[ -d ${PWD}/_dist9 ] || mkdir ${PWD}/_dist9      
	[ -d ${PWD}/_cache_dnf ] || mkdir ${PWD}/_cache_dnf
	docker run --privileged ${DOCKER_FLAGS} \
		-v ${PWD}/_dist9:/var/tmp/ \
		-v ${PWD}/_cache_dnf:/var/cache/dnf \
		ghcr.io/yashumitsu/prometheus-rpm-builder-almalinux9 \
		/bin/bash -c '/usr/bin/dnf install --verbose -y /var/tmp/${PACKAGE}*.rpm'

auto9: $(addprefix build9-,$(AUTO_GENERATED))

$(addprefix build9-,$(AUTO_GENERATED)):
	$(eval PACKAGE=$(subst build9-,,$@))

	python3 ./generate.py --templates ${PACKAGE}
	[ -d ${PWD}/_dist9 ] || mkdir ${PWD}/_dist9      
	[ -d ${PWD}/_cache_dnf ] || mkdir ${PWD}/_cache_dnf
	docker run ${DOCKER_FLAGS} \
		-v ${PWD}/${PACKAGE}:/rpmbuild/SOURCES \
		-v ${PWD}/_dist9:/rpmbuild/RPMS/x86_64 \
		-v ${PWD}/_dist9:/rpmbuild/RPMS/noarch \
		-v ${PWD}/_cache_dnf:/var/cache/dnf \
		ghcr.io/yashumitsu/prometheus-rpm-builder-almalinux9 \
		build-spec SOURCES/autogen_${PACKAGE}.spec
	# Test the install
	[ -d ${PWD}/_dist9 ] || mkdir ${PWD}/_dist9      
	[ -d ${PWD}/_cache_dnf ] || mkdir ${PWD}/_cache_dnf
	docker run --privileged ${DOCKER_FLAGS} \
		-v ${PWD}/_dist9:/var/tmp/ \
		-v ${PWD}/_cache_dnf:/var/cache/dnf \
		ghcr.io/yashumitsu/prometheus-rpm-builder-almalinux9 \
		/bin/bash -c '/usr/bin/dnf install --verbose -y /var/tmp/${PACKAGE}*.rpm'

sign9:
	docker run --rm \
		-v ${PWD}/_dist9:/rpmbuild/RPMS/x86_64 \
		-v ${PWD}/bin:/rpmbuild/bin \
		-v ${PWD}/RPM-GPG-KEY-prometheus-rpm:/rpmbuild/RPM-GPG-KEY-prometheus-rpm \
		-v ${PWD}/secret.asc:/rpmbuild/secret.asc \
		-v ${PWD}/.passphrase:/rpmbuild/.passphrase \
		ghcr.io/yashumitsu/prometheus-rpm-builder-almalinux9 \
		bin/sign

$(foreach \
	PACKAGE,$(MANUAL),$(eval \
		${PACKAGE}: \
			$(addprefix build9-,${PACKAGE}) \
	) \
)

$(foreach \
	PACKAGE,$(AUTO_GENERATED),$(eval \
		${PACKAGE}: \
			$(addprefix build9-,${PACKAGE}) \
	) \
)

sign: sign9

publish9: sign9
	package_cloud push --skip-errors yashumitsu/prometheus-rpm/el/9 _dist9/*.rpm

publish: publish9

clean:
	rm -rf _cache_dnf _cache_yum _dist*
	rm -f **/*.tar.gz
	rm -f **/*.jar
	rm -f **/autogen_*{default,init,unit,spec}
