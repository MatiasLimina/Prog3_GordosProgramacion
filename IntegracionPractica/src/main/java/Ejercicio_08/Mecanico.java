package Ejercicio_08;

import java.util.ArrayList;
import java.util.List;

public class Mecanico extends Persona {
    private double salario;
    private String turno;
    private List<TipoAvion> tiposMantenimiento;
    private List<Servicio> serviciosRealizados;

    public Mecanico(String nss, String nombre, String direccion, String telefono, double salario, String turno) {
        super(nss, nombre, direccion, telefono);
        this.salario = salario;
        this.turno = turno;
        this.tiposMantenimiento = new ArrayList<>();
        this.serviciosRealizados = new ArrayList<>();
    }

    public void agregarTipoMantenimiento(TipoAvion t) {
        if (!tiposMantenimiento.contains(t)) {
            tiposMantenimiento.add(t);
        }
    }

    public void registrarServicio(Servicio s) {
        if (!serviciosRealizados.contains(s)) {
            serviciosRealizados.add(s);
        }
    }

    public double getSalario() { return salario; }
    public void setSalario(double salario) { this.salario = salario; }

    public String getTurno() { return turno; }
    public void setTurno(String turno) { this.turno = turno; }

    public List<TipoAvion> getTiposMantenimiento() { return tiposMantenimiento; }

    public List<Servicio> getServiciosRealizados() { return serviciosRealizados; }
}
