# k8s-test: On-Prem Kubernetes Cluster + FastAPI Deployment

A small FastAPI app, containerized & deployed to a self-managed, on-prem Kubernetes cluster built with `kubeadm`, `containerd`, and Flannel.

## Cluster Overview

| Node | Role | Notes |
|---|---|---|
| `k8s-ctrl` | control-plane | Also schedules workloads (control-plane taint removed) |
| `k8s-node-1` | worker | |
| `k8s-node-2` | worker | |
| `k8s-node-3` | worker | |

- **Container runtime:** containerd (`SystemdCgroup = true`)
- **CNI:** Flannel (`kube-flannel.yml`, pod CIDR `10.244.0.0/16`)
- **k8s version:** v1.30.x
- **Provisioning:** VMs (Proxmox, `ens18` interface), static IPs via netplan

## Cluster Setup

### 1. Node prep (all nodes)
```bash
sudo swapoff -a
sudo sed -i '/ swap / s/^/#/' /etc/fstab
```
Configure static networking via `/etc/netplan/01-static-cfg.yaml`, then:
```bash
sudo chmod 600 /etc/netplan/01-static-cfg.yaml
sudo netplan apply
```

### 2. Install containerd
```bash
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml > /dev/null
```
Edit `/etc/containerd/config.toml` and set:
```toml
[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
  SystemdCgroup = true
```
```bash
sudo systemctl restart containerd
sudo systemctl enable containerd
```

### 3. Install kubeadm, kubelet, kubectl
```bash
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key \
  | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /' \
  | sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt update
sudo apt install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
```

### 4. Initialize the control plane
```bash
sudo kubeadm config images pull
sudo kubeadm init --pod-network-cidr=10.244.0.0/16

mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

Install Flannel:
```bash
wget https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
kubectl apply -f kube-flannel.yml
```

Allow the control plane to run workloads (single control-plane / small cluster):
```bash
kubectl taint nodes --all node-role.kubernetes.io/control-plane-
```

### 5. Join workers
```bash
kubeadm token create --print-join-command
```
Run the printed `kubeadm join ...` command on each worker node.

## Known Issues & Fixes

### Control-plane IP change breaks cluster
Changing the control-plane node's IP (e.g. `192.168.0.20` → `192.168.2.20`) invalidates the API server certificate and every kubeconfig that points at the old IP. To recover:

```bash
# Regenerate the API server cert with the new IP in the SAN list
sudo rm -f /etc/kubernetes/pki/apiserver.crt /etc/kubernetes/pki/apiserver.key
sudo kubeadm init phase certs apiserver --apiserver-cert-extra-sans=<NEW_IP>

# Point kubeconfigs at the new IP
sudo sed -i 's/<OLD_IP>/<NEW_IP>/g' /etc/kubernetes/admin.conf
sudo sed -i 's/<OLD_IP>/<NEW_IP>/g' /etc/kubernetes/kubelet.conf

sudo systemctl restart containerd kubelet
```
Flannel also caches node public IPs/subnets as annotations — clear and let it re-populate them:
```bash
kubectl annotate node <node> flannel.alpha.kubernetes.io/public-ip- \
  flannel.alpha.kubernetes.io/backend-data- \
  flannel.alpha.kubernetes.io/subnets-
```
> **Lesson learned:** avoid changing the control-plane node's IP after `kubeadm init`. If the IP must change, plan for a cert regeneration + kubeconfig update + Flannel annotation reset, or just re-`kubeadm init` on a clean slate (see below).

### Full node reset (used repeatedly while debugging)
```bash
sudo kubeadm reset -f
sudo systemctl stop kubelet containerd
sudo rm -rf /etc/kubernetes/ /var/lib/kubelet/ /var/lib/etcd/ /var/lib/cni/ /etc/cni/net.d/
rm -rf $HOME/.kube
sudo ip link delete flannel.1 2>/dev/null
sudo ip link delete cni0 2>/dev/null
sudo iptables -F && sudo iptables -X && sudo iptables -t nat -F && sudo iptables -t nat -X
sudo systemctl start containerd
```

### Pods stuck in `ContainerCreating`
Usually a CNI/network problem on that specific node. Checklist:
```bash
kubectl describe pod <pod> -n <ns>          # check Events
sudo systemctl restart containerd kubelet
sudo cat /etc/cni/net.d/10-flannel.conflist # confirm flannel config is present
kubectl rollout restart daemonset kube-flannel-ds -n kube-flannel
sudo conntrack -F
```

### Reference: working Flannel CNI config
Known-good `/etc/cni/net.d/10-flannel.conflist` (from `k8s-node-3`). If a node has CNI issues, compare its conflist against this — a missing or malformed file here is a common cause of pods stuck in `ContainerCreating`:
```json
{
  "name": "cbr0",
  "cniVersion": "0.3.1",
  "plugins": [
    {
      "type": "flannel",
      "delegate": {
        "hairpinMode": true,
        "isDefaultGateway": true
      }
    },
    {
      "type": "portmap",
      "capabilities": {
        "portMappings": true
      }
    }
  ]
}
```

### DNS / `resolv.conf` fights with systemd-resolved
Repeated symptom: `ping google.com` fails after every reboot/netplan apply. Fix:
```bash
sudo ln -sf /run/systemd/resolve/resolv.conf /etc/resolv.conf
sudo systemctl restart systemd-resolved
```

## Application

FastAPI app in [`app/`](./app), containerized via [`Dockerfile`](./Dockerfile).

### Build & push
```bash
docker build -t geoffreysakora/k8s-test:<tag> .
docker push geoffreysakora/k8s-test:<tag>
```

### Deploy
```bash
kubectl apply -f deployment.yml -n k8s-test
```
Exposed as a `NodePort` service (see `k8s-test` service, port `32002`), reachable at:
```
http://<any-node-ip>:32002
```

### Common operational commands
```bash
kubectl get pods -n k8s-test -o wide
kubectl logs <pod> -n k8s-test
kubectl rollout restart deployment/k8s-test -n k8s-test
kubectl scale deployment/k8s-test -n k8s-test --replicas=<n>
kubectl rollout undo deployment/k8s-test -n k8s-test --to-revision=<n>
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data
kubectl uncordon <node>
```

## Repo Structure
```
.
├── Dockerfile
├── app/
│   ├── __init__.py
│   └── main.py
├── deployment.yml
└── requirements.txt
```

## TODO
- [ ] Investigate root cause of node-1 `ContainerCreating` hangs (recurring)
- [ ] Move NodePort → Ingress or LoadBalancer (MetalLB) for cleaner external access
- [ ] Pin control-plane IP / document static IP requirement clearly before future rebuilds
- [ ] Add readiness/liveness probes to `deployment.yml`
- [ ] Automate node prep + kubeadm init with a script or Ansible playbook